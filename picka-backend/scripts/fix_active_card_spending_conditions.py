"""Backfill verified spending requirements for currently held persona cards."""

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import CardBenefit


REQUIRED_SPENDING_BY_SOURCE_ID = {
    "2358-01": 500_000,
    "2358-02": 500_000,
    "2358-03": 500_000,
    "2358-04": 500_000,
    "718-02": 300_000,
    "718-03": 300_000,
    "718-04": 300_000,
    "718-05": 300_000,
    "87-02": 300_000,
}


def main() -> None:
    with SessionLocal() as db:
        benefits = list(
            db.scalars(
                select(CardBenefit).where(
                    CardBenefit.source_benefit_id.in_(
                        REQUIRED_SPENDING_BY_SOURCE_ID
                    )
                )
            ).all()
        )
        found = {benefit.source_benefit_id for benefit in benefits}
        missing = set(REQUIRED_SPENDING_BY_SOURCE_ID) - found
        if missing:
            raise RuntimeError(f"benefits not found: {sorted(missing)}")

        for benefit in benefits:
            amount = REQUIRED_SPENDING_BY_SOURCE_ID[benefit.source_benefit_id]
            benefit.required_spending = amount
            if not benefit.condition_text:
                benefit.condition_text = f"전월 이용금액 {amount:,}원 이상"

        db.commit()
        print(f"updated {len(benefits)} verified spending requirements")


if __name__ == "__main__":
    main()
