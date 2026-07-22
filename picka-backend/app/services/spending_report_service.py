from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Card, Transaction, TransactionReward, User
from app.services.category_normalization import normalize_payment_category


REPORT_CATEGORY_MAP = {
    "푸드/외식": "식비",
    "카페/디저트": "식비",
    "배달앱": "식비",
    "편의점": "식비",
    "마트/쇼핑": "쇼핑",
    "온라인쇼핑": "쇼핑",
    "백화점": "쇼핑",
    "뷰티/피트니스": "쇼핑",
    "생활": "생활비",
    "공과금/생활요금": "생활비",
    "통신": "생활비",
    "보험": "생활비",
    "병원/약국": "생활비",
    "교통": "교통",
    "주유": "교통",
    "자동차/정비": "교통",
    "영화/문화": "문화",
    "구독/멤버십": "문화",
    "테마파크/레저": "문화",
    "여행/숙박": "문화",
}
REPORT_CATEGORY_ORDER = ["식비", "쇼핑", "생활비", "교통", "문화", "기타"]


class SpendingReportUserNotFoundError(Exception):
    pass


def previous_month(usage_month: str) -> str:
    year, month = map(int, usage_month.split("-"))
    if month == 1:
        return f"{year - 1}-12"
    return f"{year}-{month - 1:02d}"


def report_category(payment_category: str | None) -> str:
    normalized = normalize_payment_category(payment_category)
    return REPORT_CATEGORY_MAP.get(normalized or "", "기타")


def _month_rows(db: Session, user_id: int, usage_month: str):
    return db.execute(
        select(Transaction, Card)
        .join(Card, Card.id == Transaction.card_id)
        .where(
            Transaction.user_id == user_id,
            Transaction.usage_month == usage_month,
            Transaction.status == "APPROVED",
        )
        .order_by(Transaction.approved_at)
    ).all()


def _daily_cumulative(rows) -> list[dict[str, int]]:
    daily: dict[int, int] = defaultdict(int)
    for transaction, _ in rows:
        approved_at: datetime = transaction.approved_at
        daily[approved_at.day] += transaction.original_payment_amount
    cumulative = 0
    points = []
    for day in sorted(daily):
        cumulative += daily[day]
        points.append({"day": day, "amount": cumulative})
    return points


def build_monthly_spending_report(
    db: Session,
    *,
    user_id: int,
    usage_month: str,
) -> dict[str, Any]:
    if db.get(User, user_id) is None:
        raise SpendingReportUserNotFoundError(
            f"사용자 ID {user_id}를 찾을 수 없습니다."
        )

    previous_usage_month = previous_month(usage_month)
    current_rows = _month_rows(db, user_id, usage_month)
    previous_rows = _month_rows(db, user_id, previous_usage_month)
    current_total = sum(row.original_payment_amount for row, _ in current_rows)
    previous_total = sum(row.original_payment_amount for row, _ in previous_rows)
    current_benefit = sum(row.saved_amount for row, _ in current_rows)
    previous_benefit = sum(row.saved_amount for row, _ in previous_rows)
    reward_rows = db.execute(
        select(
            TransactionReward.reward_type,
            TransactionReward.reward_program,
            TransactionReward.reward_unit,
            func.sum(TransactionReward.reward_amount),
        )
        .join(Transaction, Transaction.id == TransactionReward.transaction_id)
        .where(
            Transaction.user_id == user_id,
            Transaction.usage_month == usage_month,
            Transaction.status == "APPROVED",
        )
        .group_by(
            TransactionReward.reward_type,
            TransactionReward.reward_program,
            TransactionReward.reward_unit,
        )
    ).all()

    category_amounts: dict[str, int] = defaultdict(int)
    card_benefits: dict[int, dict[str, Any]] = {}
    for transaction, card in current_rows:
        category_amounts[report_category(transaction.payment_category)] += (
            transaction.original_payment_amount
        )
        card_item = card_benefits.setdefault(card.id, {
            "cardId": card.id,
            "cardName": card.card_name,
            "issuer": card.issuer or "",
            "imageUrl": card.image_url,
            "benefit": 0,
        })
        card_item["benefit"] += transaction.saved_amount

    categories = []
    for category in REPORT_CATEGORY_ORDER:
        amount = category_amounts[category]
        categories.append({
            "category": category,
            "amount": amount,
            "ratio": round(amount / current_total * 100, 1) if current_total else 0.0,
        })

    return {
        "month": usage_month,
        "totalSpending": current_total,
        "previousMonth": previous_usage_month,
        "previousMonthSpending": previous_total,
        "spendingDifference": current_total - previous_total,
        "dailyCumulative": _daily_cumulative(current_rows),
        "previousDailyCumulative": _daily_cumulative(previous_rows),
        "totalBenefit": current_benefit,
        "previousMonthBenefit": previous_benefit,
        "benefitDifference": current_benefit - previous_benefit,
        "rewards": [
            {
                "type": reward_type,
                "program": program,
                "unit": unit,
                "amount": float(amount),
            }
            for reward_type, program, unit, amount in reward_rows
        ],
        "cardBenefits": sorted(
            card_benefits.values(), key=lambda item: item["benefit"], reverse=True
        ),
        "categories": categories,
    }
