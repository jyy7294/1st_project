from __future__ import annotations

import csv
from pathlib import Path

from sqlalchemy import delete, func, select

from app.core.database import SessionLocal
from app.models import CardRecommendationSnapshot, MerchantAlias, Transaction
from app.services.category_normalization import normalize_payment_category


CSV_PATH = Path(__file__).resolve().parents[1] / "merchant_category_corrections_apply.csv"


def _true(value: str | None) -> bool:
    return (value or "").strip().upper() == "TRUE"


def main() -> None:
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as file:
        rows = [row for row in csv.DictReader(file) if _true(row["needs_backend_apply"])]

    with SessionLocal() as db:
        aliases_by_name = {
            alias.alias: alias for alias in db.scalars(select(MerchantAlias)).all()
        }
        inserted = 0
        updated_aliases = 0
        for row in rows:
            alias_name = row["merchant_name"].strip()
            benefit_category = normalize_payment_category(
                row["recommended_benefit_match_category"]
            ) or row["recommended_benefit_match_category"].strip()
            report_category = normalize_payment_category(
                row["recommended_report_category"]
            ) or row["recommended_report_category"].strip()
            alias = aliases_by_name.get(alias_name)
            if alias is None:
                alias = MerchantAlias(
                    alias=alias_name,
                    canonical_merchant=(
                        row["alias_canonical_merchant"].strip() or alias_name
                    ),
                    category=benefit_category,
                    report_category=report_category,
                    match_type="normalized_contains",
                    priority=200,
                    source="category_correction",
                )
                db.add(alias)
                aliases_by_name[alias_name] = alias
                inserted += 1
            else:
                alias.category = benefit_category
                alias.report_category = report_category
                alias.priority = max(alias.priority or 0, 200)
                alias.source = "category_correction"
                updated_aliases += 1

        transaction_updates = 0
        correction_by_merchant = {
            row["merchant_name"].strip(): (
                normalize_payment_category(row["recommended_benefit_match_category"])
                or row["recommended_benefit_match_category"].strip()
            )
            for row in rows
        }
        for transaction in db.scalars(select(Transaction)).all():
            corrected = correction_by_merchant.get(transaction.merchant_name.strip())
            if corrected and transaction.payment_category != corrected:
                transaction.payment_category = corrected
                transaction_updates += 1

        snapshots_invalidated = db.scalar(
            select(func.count()).select_from(CardRecommendationSnapshot)
        ) or 0
        db.execute(delete(CardRecommendationSnapshot))
        db.commit()

    print(f"corrections={len(rows)}")
    print(f"aliases_inserted={inserted}")
    print(f"aliases_updated={updated_aliases}")
    print(f"transactions_updated={transaction_updates}")
    print(f"recommendation_snapshots_invalidated={snapshots_invalidated}")


if __name__ == "__main__":
    main()
