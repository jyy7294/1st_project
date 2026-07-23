from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import delete, select

from app.core.database import SessionLocal
from app.models import (
    BenefitUsage,
    Card,
    CardBenefit,
    CardRecommendationSnapshot,
    MonthlyCardUsage,
    Transaction,
    User,
    UserCard,
    UserEligibility,
    UserPersonaProfile,
)


SEED_PATH = (
    Path(__file__).resolve().parents[1]
    / "PICKA_supabase_core_seed_v8_7_age_updated.json"
)
PERSONA_USER_IDS = {
    "persona1": 1,
    "persona2": 3,
    "persona3": 4,
    "persona4": 5,
}
KST = timezone(timedelta(hours=9))

ELIGIBILITY_MAPPING = {
    "age_group": "AGE_GROUP",
    "is_student": "STUDENT",
    "military_service_target": "MILITARY_SERVICE",
    "is_business_owner": "BUSINESS_OWNER",
    "owns_light_car": "COMPACT_CAR_OWNER",
    "pregnancy_childcare_support_eligible": (
        "PREGNANCY_CHILDCARE_SUPPORT_ELIGIBLE"
    ),
    "welfare_benefit_eligible": "WELFARE_BENEFIT_ELIGIBLE",
    "occupation_qualifications": "OCCUPATION_QUALIFICATIONS",
    "telecom_provider": "TELECOM_PROVIDER",
    "primary_transport": "PRIMARY_TRANSPORT",
    "kpass_user": "KPASS_USER",
    "highpass_user": "HIGHPASS_USER",
    "preferred_airline": "PREFERRED_AIRLINE",
    "primary_shopping_affiliation": "PRIMARY_SHOPPING_AFFILIATION",
    "vehicle_owner": "VEHICLE_OWNER",
    "has_children": "HAS_CHILDREN",
    "children_count": "CHILDREN_COUNT",
    "child_age_groups": "CHILD_AGE_GROUPS",
    "detailed_age_band": "DETAILED_AGE_BAND",
}
CONFIRMED_OVERRIDES = {
    "persona2": {"MILITARY_SERVICE": ("false", "SELF_REPORTED")},
    "persona3": {"MILITARY_SERVICE": ("false", "SELF_REPORTED")},
}


def _serialize(value: object) -> str:
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def _rows_by_persona(tables: dict, table_name: str, persona_id: str) -> list:
    return [
        row for row in tables.get(table_name, [])
        if row.get("persona_id") == persona_id
    ]


def _source_payload(
    data: dict,
    profile: dict,
    persona_id: str,
) -> dict:
    tables = data["tables"]
    return {
        "metadata": data.get("metadata", {}),
        "profile": profile,
        **{
            table_name: _rows_by_persona(tables, table_name, persona_id)
            for table_name in (
                "persona_preferences",
                "user_cards",
                "transactions",
                "monthly_card_usage",
                "benefit_usage",
                "recommendation_logs",
                "calculation_audit",
                "monthly_persona_summary",
                "non_core_category_summary",
                "non_core_category_change_log",
                "persona_eligibility",
                "persona_eligibility_evidence",
                "spend_adjustment_summary",
                "age_adjustment_summary",
            )
        },
    }


def main() -> None:
    data = json.loads(SEED_PATH.read_text(encoding="utf-8-sig"))
    tables = data["tables"]
    profiles = {row["persona_id"]: row for row in tables["profiles"]}
    preferences = {
        row["persona_id"]: row for row in tables["persona_preferences"]
    }
    eligibility_rows = {
        row["persona_id"]: row for row in tables["persona_eligibility"]
    }
    source_card_ids = {row["card_id"] for row in tables["user_cards"]}
    source_benefit_ids = {
        row["benefit_id"] for row in tables["benefit_usage"]
    }
    counts = defaultdict(int)
    now = datetime.now(timezone.utc)

    with SessionLocal() as db:
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
            profile = profiles[persona_id]
            user = db.get(User, user_id)
            if user is None:
                raise RuntimeError(f"DB에 없는 사용자 ID: {user_id}")
            user.email = profile["email"]
            user.name = profile["name"]

            persona_profile = db.scalar(
                select(UserPersonaProfile).where(
                    UserPersonaProfile.user_id == user_id
                )
            )
            if persona_profile is None:
                persona_profile = UserPersonaProfile(
                    user_id=user_id,
                    persona_id=persona_id,
                    age=profile["age"],
                    source_payload={},
                )
                db.add(persona_profile)
            persona_profile.persona_id = persona_id
            persona_profile.age = profile["age"]
            persona_profile.gender = profile.get("gender")
            persona_profile.job = profile.get("job")
            persona_profile.residence = profile.get("residence")
            persona_profile.description = profile.get("description")
            persona_profile.monthly_budget = profile.get("monthly_budget")
            persona_profile.period = profile.get("period")
            persona_profile.preferred_benefits = preferences.get(
                persona_id, {}
            ).get("preferred_benefits")
            persona_profile.source_payload = _source_payload(
                data, profile, persona_id
            )
            persona_profile.source_version = data.get("metadata", {}).get(
                "dataset_version"
            )
            counts["persona_profiles"] += 1

            source_eligibility = eligibility_rows[persona_id]
            values = {
                "AGE": str(profile["age"]),
                **{
                    target: _serialize(source_eligibility.get(key, "unknown"))
                    for key, target in ELIGIBILITY_MAPPING.items()
                },
            }
            overrides = CONFIRMED_OVERRIDES.get(persona_id, {})
            values.update({key: value for key, (value, _) in overrides.items()})
            for eligibility_type, value in values.items():
                row = db.scalar(
                    select(UserEligibility).where(
                        UserEligibility.user_id == user_id,
                        UserEligibility.eligibility_type == eligibility_type,
                    )
                )
                if row is None:
                    row = UserEligibility(
                        user_id=user_id,
                        eligibility_type=eligibility_type,
                        eligibility_value=value,
                        verification_status="UNVERIFIED",
                    )
                    db.add(row)
                override = overrides.get(eligibility_type)
                status = override[1] if override else (
                    "UNVERIFIED"
                    if value.strip().lower() in {"unknown", "[]"}
                    else "INFERRED"
                )
                row.eligibility_value = value
                row.verification_status = status
                row.verified_at = None if status == "UNVERIFIED" else now
                row.expires_at = None
                counts["eligibilities"] += 1

            db.execute(delete(Transaction).where(Transaction.user_id == user_id))
            db.execute(delete(BenefitUsage).where(BenefitUsage.user_id == user_id))
            db.execute(
                delete(MonthlyCardUsage).where(
                    MonthlyCardUsage.user_id == user_id
                )
            )
            db.execute(delete(UserCard).where(UserCard.user_id == user_id))
            db.flush()

            user_cards_by_source: dict[str, UserCard] = {}
            for source in _rows_by_persona(tables, "user_cards", persona_id):
                card = cards_by_source[source["card_id"]]
                user_card = UserCard(
                    user_id=user_id,
                    card_id=card.id,
                    nickname=source.get("usage_role"),
                    is_active=bool(source.get("is_active", True)),
                    selected_option_group=(
                        str(source["selected_option"])
                        if source.get("selected_option")
                        else None
                    ),
                    card_number_last4=source.get("last4"),
                    registration_method="V8_7_SEED",
                    registered_at=now,
                )
                db.add(user_card)
                db.flush()
                user_cards_by_source[source["user_card_id"]] = user_card
                counts["user_cards"] += 1

            benefit_totals = defaultdict(int)
            for source in _rows_by_persona(tables, "benefit_usage", persona_id):
                user_card = user_cards_by_source[source["user_card_id"]]
                benefit = benefits_by_source[source["benefit_id"]]
                db.add(BenefitUsage(
                    user_id=user_id,
                    card_id=user_card.card_id,
                    card_benefit_id=benefit.id,
                    usage_month=source["usage_month"],
                    monthly_used_amount=int(source.get("used_benefit_amount") or 0),
                    monthly_used_count=int(source.get("used_count") or 0),
                    daily_used_count=0,
                ))
                benefit_totals[(user_card.card_id, source["usage_month"])] += int(
                    source.get("used_benefit_amount") or 0
                )
                counts["benefit_usage"] += 1

            for source in _rows_by_persona(
                tables, "monthly_card_usage", persona_id
            ):
                card = cards_by_source[source["card_id"]]
                db.add(MonthlyCardUsage(
                    user_id=user_id,
                    card_id=card.id,
                    usage_month=source["usage_month"],
                    previous_month_spending=int(
                        source.get("previous_month_spend") or 0
                    ),
                    current_month_spending=int(
                        source.get("current_month_spend") or 0
                    ),
                    card_monthly_benefit_used=benefit_totals[
                        (card.id, source["usage_month"])
                    ],
                ))
                counts["monthly_card_usage"] += 1

            for source in _rows_by_persona(tables, "transactions", persona_id):
                source_user_card_id = source.get("user_card_id")
                if not source_user_card_id:
                    counts["raw_only_transactions"] += 1
                    continue
                user_card = user_cards_by_source[source_user_card_id]
                approved_at = datetime.fromisoformat(source["approved_at"])
                if approved_at.tzinfo is None:
                    approved_at = approved_at.replace(tzinfo=KST)
                amount = int(source["amount"])
                db.add(Transaction(
                    user_id=user_id,
                    user_card_id=user_card.id,
                    card_id=user_card.card_id,
                    merchant_name=source["merchant_name"],
                    payment_category=source.get("normalized_code"),
                    original_payment_amount=amount,
                    saved_amount=0,
                    final_approved_amount=amount,
                    approval_number=source["transaction_id"].upper(),
                    status="APPROVED",
                    usage_month=approved_at.strftime("%Y-%m"),
                    approved_at=approved_at,
                ))
                counts["transactions"] += 1

        db.execute(
            delete(CardRecommendationSnapshot).where(
                CardRecommendationSnapshot.user_id.in_(
                    PERSONA_USER_IDS.values()
                )
            )
        )
        db.commit()

    print(json.dumps(dict(counts), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
