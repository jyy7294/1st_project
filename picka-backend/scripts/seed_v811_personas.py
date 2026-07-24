from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import delete, func, select

from app.core.database import SessionLocal
from app.models import (
    BenefitUsage,
    Card,
    CardBenefit,
    CardRecommendationSnapshot,
    MonthlyCardUsage,
    MerchantAlias,
    Transaction,
    TransactionBenefitOutcome,
    User,
    UserCard,
    UserEligibility,
    UserPersonaProfile,
)
from app.services.category_normalization import normalize_payment_category
from app.services.monthly_benefit_limit_service import (
    enforce_monthly_card_benefit_limits,
)
from app.services.user_state_adapter import resolve_category_from_aliases


CSV_PATH = Path(__file__).resolve().parents[1] / "PICKA_persona_all_in_one_v8_11.csv"
SOURCE_VERSION = "v8_11"
BENEFIT_ID_REFERENCE_CSV: Path | None = None
PERSONA_USER_IDS = {"persona1": 1, "persona2": 2, "persona3": 3, "persona4": 4}
KST = timezone(timedelta(hours=9))
AFFECTED_MONTHS = {"2026-05", "2026-06", "2026-07"}

ELIGIBILITY_MAPPING = {
    "persona_age_group": "AGE_GROUP",
    "persona_detailed_age_band": "DETAILED_AGE_BAND",
    "eligibility_is_student": "STUDENT",
    "eligibility_military_service_target": "MILITARY_SERVICE",
    "eligibility_is_business_owner": "BUSINESS_OWNER",
    "eligibility_owns_light_car": "COMPACT_CAR_OWNER",
    "eligibility_pregnancy_childcare_support": "PREGNANCY_CHILDCARE_SUPPORT_ELIGIBLE",
    "eligibility_welfare_benefit": "WELFARE_BENEFIT_ELIGIBLE",
    "eligibility_occupation_qualifications": "OCCUPATION_QUALIFICATIONS",
    "eligibility_telecom_provider": "TELECOM_PROVIDER",
    "eligibility_primary_transport": "PRIMARY_TRANSPORT",
    "eligibility_kpass_user": "KPASS_USER",
    "eligibility_highpass_user": "HIGHPASS_USER",
    "eligibility_preferred_airline": "PREFERRED_AIRLINE",
    "eligibility_primary_shopping_affiliation": "PRIMARY_SHOPPING_AFFILIATION",
    "eligibility_vehicle_owner": "VEHICLE_OWNER",
    "eligibility_has_children": "HAS_CHILDREN",
    "eligibility_children_count": "CHILDREN_COUNT",
    "eligibility_child_age_groups": "CHILD_AGE_GROUPS",
}
CONFIRMED_OVERRIDES = {
    "persona2": {"MILITARY_SERVICE": ("false", "SELF_REPORTED")},
    "persona3": {"MILITARY_SERVICE": ("false", "SELF_REPORTED")},
}


def _int(value: str | None) -> int:
    return int(float(value)) if value else 0


def _optional_int(value: str | None) -> int | None:
    return _int(value) if value else None


def _list_value(value: str | None) -> str:
    items = [item.strip() for item in (value or "").split("|") if item.strip()]
    return json.dumps(items, ensure_ascii=False)


def _list(value: str | None) -> list[str]:
    return [item.strip() for item in (value or "").split("|") if item.strip()]


def _date(value: str | None):
    return datetime.strptime(value, "%Y-%m-%d").date() if value else None


def _bool(value: str | None) -> bool:
    return (value or "").strip().lower() in {"true", "1", "yes", "y"}


def _previous_month(usage_month: str) -> str:
    year, month = map(int, usage_month.split("-"))
    return f"{year - 1}-12" if month == 1 else f"{year}-{month - 1:02d}"


def main() -> None:
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as file:
        all_rows = list(csv.DictReader(file))
    if BENEFIT_ID_REFERENCE_CSV is not None:
        with BENEFIT_ID_REFERENCE_CSV.open(
            encoding="utf-8-sig", newline=""
        ) as file:
            reference_by_approval = {
                row["approval_number_for_db"].upper(): row
                for row in csv.DictReader(file)
            }
        for row in all_rows:
            reference = reference_by_approval.get(
                row.get("approval_number_for_db", "").upper()
            )
            if reference is not None:
                # Spreadsheet programs converted IDs such as 2423-01 into
                # Jan-23 in v8.18. Approval numbers are stable across versions,
                # so restore only this corrupted identifier from v8.14.
                row["card_benefit_source_id"] = reference.get(
                    "card_benefit_source_id", ""
                )
                # The same spreadsheet conversion changed 2026-05 into May-26.
                row["usage_month"] = reference.get("usage_month", "")
    rows = [
        row for row in all_rows
        if row.get("payment_source_type") == "CARD"
        and row.get("actual_user_card_id")
        and row.get("actual_card_id")
    ]
    excluded_non_card = len(all_rows) - len(rows)
    by_persona: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_persona[row["persona_id"]].append(row)

    source_card_ids = {
        _int(row["actual_card_id"]) for row in rows
    } | {
        _int(row["recommended_card_id"])
        for row in rows if row.get("recommended_card_id")
    }
    source_benefit_ids = {
        row["card_benefit_source_id"]
        for row in rows if row.get("card_benefit_source_id")
    }
    counts = defaultdict(int)
    now = datetime.now(timezone.utc)

    with SessionLocal() as db:
        merchant_aliases = list(db.scalars(select(MerchantAlias)).all())
        cards = db.scalars(
            select(Card).where(Card.source_card_id.in_(source_card_ids))
        ).all()
        cards_by_source = {card.source_card_id: card for card in cards}
        missing_cards = source_card_ids - set(cards_by_source)
        if missing_cards:
            raise RuntimeError(f"DB에 없는 source_card_id: {sorted(missing_cards)}")

        benefits = db.scalars(
            select(CardBenefit).where(
                CardBenefit.source_benefit_id.in_(source_benefit_ids)
            )
        ).all()
        benefits_by_source = {
            benefit.source_benefit_id: benefit for benefit in benefits
        }
        missing_benefits = source_benefit_ids - set(benefits_by_source)
        if missing_benefits:
            raise RuntimeError(
                f"DB에 없는 source_benefit_id: {sorted(missing_benefits)}"
            )

        for persona_id, user_id in PERSONA_USER_IDS.items():
            persona_rows = by_persona[persona_id]
            first = persona_rows[0]
            user = db.get(User, user_id)
            if user is None:
                raise RuntimeError(f"DB에 없는 사용자 ID: {user_id}")
            user.name = first["persona_name"]
            user.email = first["persona_email"]

            profile = db.scalar(
                select(UserPersonaProfile).where(UserPersonaProfile.user_id == user_id)
            )
            if profile is None:
                profile = UserPersonaProfile(
                    user_id=user_id,
                    persona_id=persona_id,
                    age=_int(first["persona_age"]),
                    source_payload={},
                )
                db.add(profile)
            profile.persona_id = persona_id
            profile.age = _int(first["persona_age"])
            profile.birth_date = _date(first.get("persona_birth_date"))
            profile.phone_number = first.get("persona_phone_number") or None
            profile.memberships = _list(first.get("persona_memberships"))
            profile.gender = first["persona_gender"] or None
            profile.job = first["persona_job"] or None
            profile.residence = first["persona_residence"] or None
            profile.is_foreigner = _bool(first.get("persona_is_foreigner"))
            profile.residence_sido = first.get("persona_residence_sido") or None
            profile.residence_sigungu = first.get("persona_residence_sigungu") or None
            profile.child_count = _int(first.get("persona_child_count"))
            profile.children_age_reference_date = _date(
                first.get("persona_children_age_reference_date")
            )
            profile.children = json.loads(first.get("persona_children_json") or "[]")
            profile.description = first["persona_description"] or None
            profile.monthly_budget = _optional_int(first["persona_monthly_budget"])
            profile.period = first["persona_period"] or None
            profile.preferred_benefits = first["persona_preferred_benefits"] or None
            payload = dict(profile.source_payload or {})
            payload[f"{SOURCE_VERSION}_rows"] = persona_rows
            payload[f"{SOURCE_VERSION}_excludes_non_card_expenses"] = True
            profile.source_payload = payload
            profile.source_version = SOURCE_VERSION
            counts["persona_profiles"] += 1

            # v8.13은 unknown 자격을 제거한 시드다. 멤버십 열이 없다는 것은
            # 가입된 멤버십이 없다고 명시하여 제휴 혜택이 확인 대기로 남지 않게 한다.
            values = {
                "AGE": first["persona_age"],
                "MEMBERSHIPS": json.dumps(profile.memberships, ensure_ascii=False),
                "FOREIGNER": str(profile.is_foreigner).lower(),
                "RESIDENCE_SIDO": profile.residence_sido or "unknown",
                "RESIDENCE_SIGUNGU": profile.residence_sigungu or "unknown",
                "CHILDREN_DETAILS": json.dumps(profile.children, ensure_ascii=False),
            }
            for source_key, target in ELIGIBILITY_MAPPING.items():
                value = first.get(source_key, "")
                if target in {"OCCUPATION_QUALIFICATIONS", "CHILD_AGE_GROUPS"}:
                    value = _list_value(value)
                values[target] = (
                    value
                    if target == "DETAILED_AGE_BAND"
                    else value or "unknown"
                )
            overrides = CONFIRMED_OVERRIDES.get(persona_id, {})
            values.update({key: value for key, (value, _) in overrides.items()})
            for eligibility_type, value in values.items():
                if eligibility_type == "DETAILED_AGE_BAND" and not value.strip():
                    db.execute(
                        delete(UserEligibility).where(
                            UserEligibility.user_id == user_id,
                            UserEligibility.eligibility_type == eligibility_type,
                        )
                    )
                    continue
                eligibility = db.scalar(
                    select(UserEligibility).where(
                        UserEligibility.user_id == user_id,
                        UserEligibility.eligibility_type == eligibility_type,
                    )
                )
                if eligibility is None:
                    eligibility = UserEligibility(
                        user_id=user_id,
                        eligibility_type=eligibility_type,
                        eligibility_value=value,
                        verification_status="UNVERIFIED",
                    )
                    db.add(eligibility)
                source_status = first.get("eligibility_verification_status", "")
                status = (
                    "VERIFIED"
                    if source_status.strip().upper() == "VERIFIED"
                    else overrides.get(eligibility_type, (None, None))[1]
                    or (
                        "UNVERIFIED"
                        if value.strip().lower() == "unknown"
                        else "INFERRED"
                    )
                )
                eligibility.eligibility_value = value
                eligibility.verification_status = status
                eligibility.verified_at = None if status == "UNVERIFIED" else now
                eligibility.expires_at = None
                counts["eligibilities"] += 1

            user_cards = db.scalars(
                select(UserCard).where(UserCard.user_id == user_id)
            ).all()
            user_cards_by_card_id = {item.card_id: item for item in user_cards}
            for row in persona_rows:
                card = cards_by_source[_int(row["actual_card_id"])]
                user_card = user_cards_by_card_id.get(card.id)
                if user_card is None:
                    raise RuntimeError(
                        f"{persona_id}에 없는 보유 카드: {row['actual_card_name']}"
                    )
                user_card.nickname = row["actual_card_usage_role"] or user_card.nickname
                user_card.card_number_last4 = row["actual_card_last4"] or user_card.card_number_last4

            csv_approvals = {row["approval_number_for_db"].upper() for row in persona_rows}
            stale = db.scalars(
                select(Transaction).where(
                    Transaction.user_id == user_id,
                    Transaction.data_source == "SEED",
                    Transaction.usage_month.in_(AFFECTED_MONTHS),
                    Transaction.approval_number.not_in(csv_approvals),
                )
            ).all()
            counts["deleted_stale_seed_transactions"] += len(stale)
            for transaction in stale:
                db.delete(transaction)
            db.flush()

            for row in persona_rows:
                approval = row["approval_number_for_db"].upper()
                transaction = db.scalar(
                    select(Transaction).where(Transaction.approval_number == approval)
                )
                card = cards_by_source[_int(row["actual_card_id"])]
                user_card = user_cards_by_card_id[card.id]
                approved_at = datetime.fromisoformat(row["approved_at"])
                if approved_at.tzinfo is None:
                    approved_at = approved_at.replace(tzinfo=KST)
                saved_amount = _int(row["saved_amount"])
                if transaction is None:
                    transaction = Transaction(
                        user_id=user_id,
                        user_card_id=user_card.id,
                        card_id=card.id,
                        merchant_name=row["merchant_name"],
                        payment_category="기타",
                        original_payment_amount=1,
                        saved_amount=0,
                        final_approved_amount=1,
                        approval_number=approval,
                        status="APPROVED",
                        usage_month=row["usage_month"],
                        approved_at=approved_at,
                        data_source="SEED",
                    )
                    db.add(transaction)
                    db.flush()
                    counts["inserted_transactions"] += 1
                elif transaction.data_source != "SEED":
                    raise RuntimeError(f"DEMO 승인번호와 CSV가 충돌합니다: {approval}")
                else:
                    counts["updated_transactions"] += 1
                transaction.user_card_id = user_card.id
                transaction.card_id = card.id
                transaction.merchant_name = row["merchant_name"]
                alias_category = resolve_category_from_aliases(
                    merchant_aliases,
                    row["merchant_name"],
                )
                transaction.payment_category = (
                    normalize_payment_category(
                        alias_category or row["payment_category"]
                    )
                    or alias_category
                    or row["payment_category"]
                )
                transaction.original_payment_amount = _int(row["original_payment_amount"])
                transaction.saved_amount = saved_amount
                transaction.final_approved_amount = _int(row["final_approved_amount"])
                transaction.applied_benefit_name = (
                    row["card_benefit_name"] or row["card_benefit_source_summary"] or None
                    if saved_amount > 0 else None
                )
                transaction.applied_benefit_category = (
                    row["card_benefit_category"] or None if saved_amount > 0 else None
                )
                transaction.status = row["transaction_status"] or "APPROVED"
                transaction.usage_month = row["usage_month"]
                transaction.approved_at = approved_at
                transaction.data_source = "SEED"
                transaction.demo_session_id = None
                db.flush()

                outcome = db.scalar(
                    select(TransactionBenefitOutcome).where(
                        TransactionBenefitOutcome.transaction_id == transaction.id
                    )
                )
                if outcome is None:
                    outcome = TransactionBenefitOutcome(
                        transaction_id=transaction.id,
                        benefit_scenario=row["benefit_scenario"],
                        picka_usage_stage=row["picka_usage_stage"],
                        actual_benefit_amount=0,
                        potential_benefit_amount=0,
                        missed_benefit_amount=0,
                        raw_data={},
                    )
                    db.add(outcome)
                recommended_card = cards_by_source.get(_int(row["recommended_card_id"]))
                benefit = benefits_by_source.get(row["card_benefit_source_id"])
                outcome.recommended_card_id = recommended_card.id if recommended_card else None
                outcome.card_benefit_id = benefit.id if benefit else None
                outcome.benefit_scenario = row["benefit_scenario"]
                outcome.picka_usage_stage = row["picka_usage_stage"]
                outcome.actual_benefit_amount = _int(row["actual_benefit_amount"])
                outcome.potential_benefit_amount = _int(row["potential_benefit_amount"])
                outcome.missed_benefit_amount = _int(row["missed_benefit_amount"])
                outcome.missed_benefit_reason = row["missed_benefit_reason"] or None
                outcome.benefit_rate_text = row["benefit_rate_text"] or None
                outcome.monthly_benefit_cap = _optional_int(row["monthly_benefit_cap"])
                outcome.cap_remaining_before = _optional_int(row["cap_remaining_before"])
                outcome.cap_remaining_after = _optional_int(row["cap_remaining_after"])
                outcome.judgement_source = row["benefit_judgement_source"] or None
                outcome.reward_type = row["reward_type"] or None
                outcome.reward_program = row["reward_program"] or None
                outcome.reward_amount = _optional_int(row["reward_amount"])
                outcome.reward_unit = row["reward_unit"] or None
                outcome.raw_data = row
                counts["benefit_outcomes"] += 1

        db.flush()

        # v8.11의 실제 할인 수령분으로 해당 3개월 혜택 사용량을 다시 만듭니다.
        counts["clamped_monthly_total_limit_transactions"] = (
            enforce_monthly_card_benefit_limits(
                db,
                user_ids=list(PERSONA_USER_IDS.values()),
                usage_months=sorted(AFFECTED_MONTHS),
            )
        )
        db.flush()

        db.execute(
            delete(BenefitUsage).where(
                BenefitUsage.user_id.in_(PERSONA_USER_IDS.values()),
                BenefitUsage.usage_month.in_(AFFECTED_MONTHS),
            )
        )
        benefit_groups: dict[tuple[int, int, int, str], list[int]] = defaultdict(
            lambda: [0, 0]
        )
        corrected_transactions = db.scalars(
            select(Transaction).where(
                Transaction.user_id.in_(PERSONA_USER_IDS.values()),
                Transaction.usage_month.in_(AFFECTED_MONTHS),
                Transaction.status == "APPROVED",
                Transaction.saved_amount > 0,
            )
        ).all()
        for transaction in corrected_transactions:
            outcome = transaction.benefit_outcome
            if outcome is None or outcome.card_benefit_id is None:
                continue
            bucket = benefit_groups[(
                transaction.user_id,
                transaction.card_id,
                outcome.card_benefit_id,
                transaction.usage_month,
            )]
            bucket[0] += transaction.saved_amount
            bucket[1] += 1
        for (user_id, card_id, benefit_id, month), (amount, count) in benefit_groups.items():
            db.add(BenefitUsage(
                user_id=user_id,
                card_id=card_id,
                card_benefit_id=benefit_id,
                usage_month=month,
                monthly_used_amount=amount,
                monthly_used_count=count,
                daily_used_count=0,
            ))
            counts["benefit_usage"] += 1

        # 월 합계는 SEED와 보존된 DEMO 거래를 모두 포함해 재계산합니다.
        user_cards = db.scalars(
            select(UserCard).where(UserCard.user_id.in_(PERSONA_USER_IDS.values()))
        ).all()
        for user_card in user_cards:
            for month in sorted(AFFECTED_MONTHS):
                current = db.scalar(
                    select(func.coalesce(func.sum(Transaction.original_payment_amount), 0)).where(
                        Transaction.user_id == user_card.user_id,
                        Transaction.card_id == user_card.card_id,
                        Transaction.usage_month == month,
                        Transaction.status == "APPROVED",
                    )
                ) or 0
                if not current:
                    continue
                previous = db.scalar(
                    select(func.coalesce(func.sum(Transaction.original_payment_amount), 0)).where(
                        Transaction.user_id == user_card.user_id,
                        Transaction.card_id == user_card.card_id,
                        Transaction.usage_month == _previous_month(month),
                        Transaction.status == "APPROVED",
                    )
                ) or 0
                benefit_total = db.scalar(
                    select(func.coalesce(func.sum(Transaction.saved_amount), 0)).where(
                        Transaction.user_id == user_card.user_id,
                        Transaction.card_id == user_card.card_id,
                        Transaction.usage_month == month,
                        Transaction.status == "APPROVED",
                    )
                ) or 0
                monthly = db.scalar(
                    select(MonthlyCardUsage).where(
                        MonthlyCardUsage.user_id == user_card.user_id,
                        MonthlyCardUsage.card_id == user_card.card_id,
                        MonthlyCardUsage.usage_month == month,
                    )
                )
                if monthly is None:
                    monthly = MonthlyCardUsage(
                        user_id=user_card.user_id,
                        card_id=user_card.card_id,
                        usage_month=month,
                        previous_month_spending=0,
                        current_month_spending=0,
                        card_monthly_benefit_used=0,
                    )
                    db.add(monthly)
                monthly.previous_month_spending = int(previous)
                monthly.current_month_spending = int(current)
                monthly.card_monthly_benefit_used = int(benefit_total)
                counts["monthly_card_usage"] += 1

        db.execute(
            delete(CardRecommendationSnapshot).where(
                CardRecommendationSnapshot.user_id.in_(PERSONA_USER_IDS.values())
            )
        )
        db.commit()

    print(json.dumps({
        **dict(counts),
        "excluded_non_card_rows": excluded_non_card,
        "csv_card_rows": len(rows),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
