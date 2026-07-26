from __future__ import annotations

from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.models import MonthlyCardUsage, Transaction


def main() -> None:
    with SessionLocal() as db:
        totals = {
            (int(user_id), int(card_id), usage_month): int(amount or 0)
            for user_id, card_id, usage_month, amount in db.execute(
                select(
                    Transaction.user_id,
                    Transaction.card_id,
                    Transaction.usage_month,
                    func.sum(Transaction.saved_amount),
                )
                .where(Transaction.status == "APPROVED")
                .group_by(
                    Transaction.user_id,
                    Transaction.card_id,
                    Transaction.usage_month,
                )
            ).all()
        }
        rows = db.scalars(select(MonthlyCardUsage)).all()
        updated = 0
        for row in rows:
            expected = totals.get(
                (row.user_id, row.card_id, row.usage_month),
                0,
            )
            if row.card_monthly_benefit_used != expected:
                row.card_monthly_benefit_used = expected
                updated += 1
        db.commit()

    print(f"checked={len(rows)}")
    print(f"updated={updated}")


if __name__ == "__main__":
    main()
