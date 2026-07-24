from __future__ import annotations

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import MerchantAlias, Transaction
from app.services.category_normalization import normalize_payment_category
from app.services.user_state_adapter import resolve_category_from_aliases


def main() -> None:
    with SessionLocal() as db:
        aliases = list(db.scalars(select(MerchantAlias)).all())
        transactions = db.scalars(select(Transaction)).all()
        matched = 0
        updated = 0
        for transaction in transactions:
            category = resolve_category_from_aliases(
                aliases,
                transaction.merchant_name,
            )
            if category is None:
                continue
            matched += 1
            normalized = normalize_payment_category(category) or category
            if transaction.payment_category != normalized:
                transaction.payment_category = normalized
                updated += 1
        db.commit()

    print(f"matched={matched}")
    print(f"updated={updated}")


if __name__ == "__main__":
    main()
