from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Transaction


CONFIRMED_BENEFIT_SOURCE = "transactions.saved_amount"


def confirmed_benefit_totals_by_card(
    db: Session,
    *,
    user_id: int,
    usage_month: str,
) -> dict[int, int]:
    """승인 거래에서 실제 확정된 혜택만 카드별로 합산한다."""
    rows = db.execute(
        select(Transaction.card_id, func.coalesce(func.sum(Transaction.saved_amount), 0))
        .where(
            Transaction.user_id == user_id,
            Transaction.usage_month == usage_month,
            Transaction.status == "APPROVED",
        )
        .group_by(Transaction.card_id)
    ).all()
    return {int(card_id): int(amount or 0) for card_id, amount in rows}


def confirmed_benefit_total(
    db: Session,
    *,
    user_id: int,
    usage_month: str,
) -> int:
    """모든 API가 사용하는 사용자 월 확정 혜택 합계 기준."""
    return sum(confirmed_benefit_totals_by_card(
        db, user_id=user_id, usage_month=usage_month
    ).values())
