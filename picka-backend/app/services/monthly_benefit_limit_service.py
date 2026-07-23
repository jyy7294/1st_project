from __future__ import annotations

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Card, Transaction


def enforce_monthly_card_benefit_limits(
    db: Session,
    *,
    user_ids: list[int] | None = None,
    usage_months: list[str] | None = None,
) -> int:
    """승인 거래를 시간순으로 잘라 카드 월 통합한도 초과를 복구한다."""
    query = (
        select(Transaction, Card.monthly_total_limit)
        .join(Card, Card.id == Transaction.card_id)
        .where(
            Transaction.status == "APPROVED",
            Card.monthly_total_limit.is_not(None),
        )
        .order_by(
            Transaction.user_id,
            Transaction.card_id,
            Transaction.usage_month,
            Transaction.approved_at,
            Transaction.id,
        )
    )
    if user_ids:
        query = query.where(Transaction.user_id.in_(user_ids))
    if usage_months:
        query = query.where(Transaction.usage_month.in_(usage_months))

    running: dict[tuple[int, int, str], int] = defaultdict(int)
    changed = 0
    for transaction, monthly_total_limit in db.execute(query).all():
        key = (transaction.user_id, transaction.card_id, transaction.usage_month)
        remaining = max(int(monthly_total_limit) - running[key], 0)
        corrected = min(transaction.saved_amount, remaining)
        running[key] += corrected
        if corrected == transaction.saved_amount:
            continue
        transaction.saved_amount = corrected
        transaction.final_approved_amount = transaction.original_payment_amount - corrected
        if corrected == 0:
            transaction.applied_benefit_name = None
            transaction.applied_benefit_category = None
        if transaction.benefit_outcome is not None:
            outcome = transaction.benefit_outcome
            outcome.actual_benefit_amount = corrected
            outcome.missed_benefit_amount = max(
                outcome.missed_benefit_amount,
                outcome.potential_benefit_amount - corrected,
            )
            if not outcome.missed_benefit_reason:
                outcome.missed_benefit_reason = "카드 월 통합한도 적용"
        changed += 1
    return changed
