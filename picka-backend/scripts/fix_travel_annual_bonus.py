"""Correct the misclassified Digiloca Travel annual mileage bonus.

This is intentionally scoped to one stable source benefit ID and is idempotent.
"""

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import CardBenefit


SOURCE_BENEFIT_ID = "2863-03"


def main() -> None:
    with SessionLocal() as db:
        benefit = db.scalar(
            select(CardBenefit).where(
                CardBenefit.source_benefit_id == SOURCE_BENEFIT_ID
            )
        )
        if benefit is None:
            raise RuntimeError(f"benefit {SOURCE_BENEFIT_ID} was not found")

        conditions = dict(benefit.additional_conditions or {})
        conditions.update(
            {
                "reward_kind": "fixed_annual_bonus",
                "annual_count_limit": 1,
                "first_year_required_spending": 3_000_000,
                "later_year_required_spending": 12_000_000,
                "transaction_calculable": False,
            }
        )
        benefit.benefit_value = 15_000
        benefit.benefit_unit = "마일"
        benefit.annual_limit = 1
        benefit.limit_status = "연 1회"
        benefit.condition_text = (
            "발급 1차년도 연간 300만원 이상, "
            "발급 2차년도 이후 연간 1,200만원 이상 이용 시 연 1회"
        )
        benefit.additional_conditions = conditions
        db.commit()

        print(
            f"updated {SOURCE_BENEFIT_ID}: "
            f"{benefit.benefit_value:g}{benefit.benefit_unit}, "
            f"{benefit.limit_status}"
        )


if __name__ == "__main__":
    main()
