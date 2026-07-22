from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Card,
    CardRecommendationSnapshot,
    MerchantAlias,
    Transaction,
    User,
    UserCard,
)
from app.services.category_normalization import normalize_payment_category
from app.services.recommendation_service import calculate_card_benefit


CATEGORY_NORMALIZATION = {
    "DELIVERY": "배달앱",
    "배달": "배달앱",
    "배달앱": "배달앱",
    "MART": "마트/쇼핑",
    "마트": "마트/쇼핑",
    "대형마트": "마트/쇼핑",
    "쇼핑": "마트/쇼핑",
    "마트/쇼핑": "마트/쇼핑",
    "TUITION": "교육/육아",
    "교육": "교육/육아",
    "학원": "교육/육아",
    "육아": "교육/육아",
    "교육/육아": "교육/육아",
    "CAFE": "카페/디저트",
    "카페": "카페/디저트",
    "디저트": "카페/디저트",
    "카페/디저트": "카페/디저트",
    "DINING": "푸드/외식",
    "RESTAURANT": "푸드/외식",
    "음식점": "푸드/외식",
    "외식": "푸드/외식",
    "푸드/외식": "푸드/외식",
    "FITNESS": "뷰티/피트니스",
    "BEAUTY": "뷰티/피트니스",
    "헬스": "뷰티/피트니스",
    "피트니스": "뷰티/피트니스",
    "뷰티/피트니스": "뷰티/피트니스",
    "FUEL": "주유",
    "GAS": "주유",
    "주유": "주유",
    "INSURANCE": "보험",
    "보험": "보험",
    "CONVENIENCE": "편의점",
    "편의점": "편의점",
    "TRANSPORT": "교통",
    "TRANSIT": "교통",
    "TAXI": "교통",
    "PARKING": "교통",
    "TOLL": "교통",
    "교통": "교통",
    "MEDICAL": "병원/약국",
    "병원": "병원/약국",
    "약국": "병원/약국",
    "병원/약국": "병원/약국",
    "STATIONERY": "문구",
    "문구": "문구",
    "ACADEMY": "교육/육아",
    "CHILD_CLASS": "교육/육아",
    "ONLINE_COURSE": "교육/육아",
    "BABY": "교육/육아",
    "BOOKS": "교육/육아",
    "SHOPPING": "마트/쇼핑",
    "GROCERY": "마트/쇼핑",
    "ONLINE_GROCERY": "마트/쇼핑",
    "ONLINE_SHOPPING": "온라인쇼핑",
    "SUBSCRIPTION": "구독/멤버십",
    "TELECOM": "통신",
    "PHARMACY": "병원/약국",
    "HOUSEHOLD": "생활",
    "LIVING": "생활",
    "FURNITURE": "생활",
    "MANAGEMENT_FEE": "공과금/생활요금",
    "EASY_PAY": "간편결제",
    "AUTO": "자동차/정비",
    "RENTAL_CAR": "자동차/정비",
    "LODGING": "여행/숙박",
    "TRAVEL": "여행/숙박",
    "TRAVEL_LODGING": "여행/숙박",
    "TRAVEL_SPEND": "여행/숙박",
    "TRAVEL_TRANSIT": "여행/숙박",
    "TRAVEL_TRANSPORT": "여행/숙박",
    "MOVIE": "영화/문화",
}


class SpendingRecommendationUserNotFoundError(Exception):
    pass


def normalize_spending_category(category: str | None) -> str | None:
    return normalize_payment_category(category)


def _matches_card_type(card_type: str | None, requested_type: str) -> bool:
    value = (card_type or "").strip().lower()
    if requested_type == "credit":
        return value in {"credit", "신용", "신용카드"}
    return value in {"check", "debit", "체크", "체크카드"}


def build_monthly_spending_profile(
    db: Session,
    user_id: int,
    months: int = 3,
) -> dict[str, int]:
    recent_months = list(
        db.scalars(
            select(Transaction.usage_month)
            .where(
                Transaction.user_id == user_id,
                Transaction.status == "APPROVED",
            )
            .distinct()
            .order_by(Transaction.usage_month.desc())
            .limit(months)
        ).all()
    )
    if not recent_months:
        return {}

    rows = db.execute(
        select(
            Transaction.payment_category,
            func.sum(Transaction.original_payment_amount),
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.status == "APPROVED",
            Transaction.usage_month.in_(recent_months),
        )
        .group_by(Transaction.payment_category)
    ).all()

    totals: dict[str, int] = defaultdict(int)
    for category, amount in rows:
        normalized = normalize_spending_category(category)
        if normalized:
            totals[normalized] += int(amount or 0)

    divisor = len(recent_months)
    return {
        category: round(total / divisor)
        for category, total in totals.items()
        if total > 0
    }


def build_recent_spending_profile(
    db: Session,
    user_id: int,
    *,
    reference_date: date | None = None,
    days: int = 7,
) -> tuple[date, date, dict[str, int], list[dict[str, Any]]]:
    korea = ZoneInfo("Asia/Seoul")
    today = reference_date or datetime.now(korea).date()
    end_local = datetime.combine(today, time.min, tzinfo=korea)
    start_local = end_local - timedelta(days=days)
    start_utc = start_local.astimezone(timezone.utc)
    end_utc = end_local.astimezone(timezone.utc)
    rows = db.execute(
        select(
            Transaction.payment_category,
            func.sum(Transaction.original_payment_amount),
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.status == "APPROVED",
            Transaction.approved_at >= start_utc,
            Transaction.approved_at < end_utc,
        )
        .group_by(Transaction.payment_category)
    ).all()

    totals: dict[str, int] = defaultdict(int)
    for category, amount in rows:
        normalized = normalize_spending_category(category)
        if normalized:
            totals[normalized] += int(amount or 0)
    merchant_rows = db.execute(
        select(
            Transaction.merchant_name,
            Transaction.payment_category,
            func.sum(Transaction.original_payment_amount),
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.status == "APPROVED",
            Transaction.approved_at >= start_utc,
            Transaction.approved_at < end_utc,
        )
        .group_by(Transaction.merchant_name, Transaction.payment_category)
    ).all()
    aliases = db.scalars(select(MerchantAlias)).all()
    merchants = []
    for merchant_name, category, amount in merchant_rows:
        normalized_name = _normalize_search_text(merchant_name)
        matched_aliases = [
            alias
            for alias in aliases
            if _normalize_search_text(alias.alias) in normalized_name
        ]
        matched_alias = max(
            matched_aliases,
            key=lambda alias: (
                len(_normalize_search_text(alias.alias)),
                alias.priority or 0,
            ),
            default=None,
        )
        canonical = (
            matched_alias.canonical_merchant if matched_alias else merchant_name
        )
        search_terms = {canonical, merchant_name}
        if matched_alias:
            search_terms.add(matched_alias.alias)
        merchants.append({
            "merchant_name": merchant_name,
            "canonical_merchant": canonical,
            "category": normalize_spending_category(category),
            "amount": int(amount or 0),
            "search_terms": [term for term in search_terms if term],
        })
    merchants.sort(key=lambda item: item["amount"], reverse=True)
    return (
        start_local.date(),
        (end_local - timedelta(days=1)).date(),
        dict(totals),
        merchants[:10],
    )


def _normalize_search_text(value: str | None) -> str:
    return "".join(character.lower() for character in (value or "") if character.isalnum())


def _benefit_search_text(benefit: Any) -> str:
    conditions = benefit.additional_conditions or {}
    values = [
        benefit.benefit_name,
        benefit.source_summary,
        benefit.source_detail,
        benefit.condition_text,
        benefit.exception_text,
        conditions.get("merchant_list"),
        conditions.get("category_list"),
    ]
    return _normalize_search_text(" ".join(str(value) for value in values if value))


def _candidate_state(card: Card, monthly_spending: int) -> dict[str, Any]:
    return {
        "card_id": card.id,
        "card_name": card.card_name,
        "card_company": card.issuer,
        "card_image": card.image_url,
        "previous_month_spending": monthly_spending,
        "required_spending": card.previous_spending or 0,
        "monthly_total_limit": card.monthly_total_limit,
        "monthly_benefit_used": 0,
        "benefit_usage_this_month": {},
        "benefits": list(card.benefits),
    }


def recommend_new_cards_by_spending(
    db: Session,
    *,
    user_id: int,
    card_type: str,
    limit: int,
    reference_date: date | None = None,
) -> dict[str, Any]:
    if db.get(User, user_id) is None:
        raise SpendingRecommendationUserNotFoundError(
            f"사용자 ID {user_id}를 찾을 수 없습니다."
        )

    analysis_start, analysis_end, profile, merchant_profile = build_recent_spending_profile(
        db,
        user_id,
        reference_date=reference_date,
    )
    monthly_spending = sum(profile.values())
    top_category, top_category_spend = (
        max(profile.items(), key=lambda item: item[1])
        if profile
        else (None, 0)
    )
    owned_card_ids = select(UserCard.card_id).where(UserCard.user_id == user_id)
    cards = db.scalars(
        select(Card)
        .options(selectinload(Card.benefits))
        .where(
            Card.is_active.is_(True),
            Card.id.not_in(owned_card_ids),
        )
    ).all()

    results = []
    for card in cards:
        if not _matches_card_type(card.card_type, card_type):
            continue

        state = _candidate_state(card, monthly_spending)
        benefit_totals: dict[str, dict[str, int | None]] = {}
        best_category_result = None
        matched_merchants: set[str] = set()

        for category, amount in profile.items():
            calculation = calculate_card_benefit(
                state,
                payment_category=category,
                payment_amount=amount,
            )
            benefit = int(calculation.get("expected_benefit", 0) or 0)
            if benefit > 0:
                benefit_key = str(
                    calculation.get("benefit_name") or category
                )
                bucket = benefit_totals.setdefault(
                    benefit_key,
                    {
                        "amount": 0,
                        "monthly_limit": calculation.get("monthly_limit"),
                    },
                )
                bucket["amount"] = int(bucket["amount"] or 0) + benefit
            if (
                benefit > 0
                and (
                    best_category_result is None
                    or benefit > best_category_result["amount"]
                )
            ):
                best_category_result = {
                    "amount": benefit,
                    "name": calculation.get("benefit_name") or category,
                    "rate": calculation.get("benefit_rate") or 0,
                    "category": category,
                    "monthly_spend": amount,
                }

        for benefit_item in card.benefits:
            searchable = _benefit_search_text(benefit_item)
            if not searchable:
                continue
            for merchant in merchant_profile:
                terms = [
                    _normalize_search_text(term)
                    for term in merchant["search_terms"]
                ]
                if not any(len(term) >= 2 and term in searchable for term in terms):
                    continue
                merchant_state = {
                    **state,
                    "benefits": [benefit_item],
                }
                calculation = calculate_card_benefit(
                    merchant_state,
                    payment_category=(
                        benefit_item.category or merchant["category"] or "기타"
                    ),
                    payment_amount=merchant["amount"],
                )
                amount = int(calculation.get("expected_benefit", 0) or 0)
                if amount <= 0:
                    continue
                benefit_name = str(
                    calculation.get("benefit_name")
                    or benefit_item.benefit_name
                    or merchant["canonical_merchant"]
                )
                bucket = benefit_totals.setdefault(
                    benefit_name,
                    {
                        "amount": 0,
                        "monthly_limit": calculation.get("monthly_limit"),
                    },
                )
                bucket["amount"] = max(int(bucket["amount"] or 0), amount)
                matched_merchants.add(merchant["canonical_merchant"])
                if (
                    best_category_result is None
                    or amount > best_category_result["amount"]
                ):
                    best_category_result = {
                        "amount": amount,
                        "name": benefit_name,
                        "rate": calculation.get("benefit_rate") or 0,
                        "category": merchant["category"],
                        "monthly_spend": merchant["amount"],
                    }

        monthly_total = sum(
            min(int(bucket["amount"] or 0), int(bucket["monthly_limit"]))
            if bucket["monthly_limit"] is not None
            else int(bucket["amount"] or 0)
            for bucket in benefit_totals.values()
        )

        if card.monthly_total_limit is not None:
            monthly_total = min(monthly_total, max(card.monthly_total_limit, 0))

        fee = max(int(card.annual_fee or 0), 0)
        annual_total = max(monthly_total * 12 - fee, 0)
        best = best_category_result or {
            "name": "적용 가능한 혜택 없음",
            "rate": 0,
            "category": top_category,
            "monthly_spend": top_category_spend,
        }
        category_label = best["category"] or "주요 업종"
        recommendation_message = (
            f"최근 7일간 {category_label}에서 {int(best['monthly_spend']):,}원을 사용했어요. "
            f"이 카드를 쓰면 {best['name']} 혜택으로 "
            f"연간 약 {annual_total:,}원의 혜택을 받을 수 있어요."
            if annual_total > 0
            else f"최근 7일 {category_label} 소비에 적용 가능한 계산형 혜택이 없습니다."
        )
        results.append({
            "id": card.id,
            "name": card.card_name,
            "issuer": card.issuer or "",
            "benefitName": best["name"],
            "rate": float(best["rate"]),
            "total": annual_total,
            "fee": fee,
            "url": card.source_url,
            "image_url": card.image_url,
            "benefitCategory": best["category"],
            "monthlySpend": int(best["monthly_spend"]),
            "recommendationMessage": recommendation_message,
            "matchedMerchants": sorted(matched_merchants),
        })

    results.sort(key=lambda item: (-item["total"], item["fee"], item["id"]))
    return {
        "analysisStartDate": analysis_start.isoformat(),
        "analysisEndDate": analysis_end.isoformat(),
        "updateCycle": "daily 00:00 Asia/Seoul",
        "topCategory": top_category,
        "topCategorySpend": top_category_spend,
        "topMerchants": [
            {
                "name": item["canonical_merchant"],
                "category": item["category"],
                "amount": item["amount"],
            }
            for item in merchant_profile
        ],
        "cards": results[:limit],
    }


def get_daily_card_recommendations(
    db: Session,
    *,
    user_id: int,
    card_type: str,
    limit: int,
    force_refresh: bool = False,
) -> dict[str, Any]:
    analysis_date = datetime.now(ZoneInfo("Asia/Seoul")).date()
    snapshot = db.scalar(
        select(CardRecommendationSnapshot).where(
            CardRecommendationSnapshot.user_id == user_id,
            CardRecommendationSnapshot.analysis_date == analysis_date,
        )
    )
    if snapshot is None or force_refresh:
        credit_result = recommend_new_cards_by_spending(
            db,
            user_id=user_id,
            card_type="credit",
            limit=20,
            reference_date=analysis_date,
        )
        check_result = recommend_new_cards_by_spending(
            db,
            user_id=user_id,
            card_type="check",
            limit=20,
            reference_date=analysis_date,
        )
        if snapshot is None:
            snapshot = CardRecommendationSnapshot(
                user_id=user_id,
                analysis_date=analysis_date,
                credit_result=credit_result,
                check_result=check_result,
            )
            db.add(snapshot)
        else:
            snapshot.credit_result = credit_result
            snapshot.check_result = check_result
            snapshot.generated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(snapshot)
        cached = False
    else:
        cached = True

    payload = dict(
        snapshot.credit_result if card_type == "credit" else snapshot.check_result
    )
    payload["cards"] = payload.get("cards", [])[:limit]
    payload["cached"] = cached
    payload["generatedAt"] = snapshot.generated_at.isoformat()
    return payload
