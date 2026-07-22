from __future__ import annotations

from collections import defaultdict
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Card, Transaction, User, UserCard
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
    if not category:
        return None
    value = category.strip()
    return CATEGORY_NORMALIZATION.get(value, CATEGORY_NORMALIZATION.get(value.upper(), value))


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
) -> dict[str, list[dict[str, Any]]]:
    if db.get(User, user_id) is None:
        raise SpendingRecommendationUserNotFoundError(
            f"사용자 ID {user_id}를 찾을 수 없습니다."
        )

    profile = build_monthly_spending_profile(db, user_id)
    monthly_spending = sum(profile.values())
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
        best = best_category_result or {"name": "적용 가능한 혜택 없음", "rate": 0}
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
        })

    results.sort(key=lambda item: (-item["total"], item["fee"], item["id"]))
    return {"cards": results[:limit]}
