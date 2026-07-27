"""Apply reviewed merchant-list corrections without replacing benefit records.

The handoff's enriched CSV is authoritative only for ``가맹점목록`` here.
All other benefit fields remain untouched. The command is dry-run by default;
pass ``--apply`` to commit the verified changes.
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import CardBenefit, MerchantAlias


NULL_STRINGS = {"", "nan", "null", "none", "<na>"}
TEXT_FIELDS = (
    "benefit_name",
    "category",
    "benefit_type",
    "benefit_unit",
    "limit_status",
    "condition_text",
    "exception_text",
    "raw_text",
    "source_summary",
    "source_detail",
)


def nullify(value: Any) -> Any:
    if isinstance(value, float) and math.isnan(value):
        return None
    if isinstance(value, str) and value.strip().lower() in NULL_STRINGS:
        return None
    if isinstance(value, dict):
        return {key: nullify(item) for key, item in value.items()}
    if isinstance(value, list):
        return [nullify(item) for item in value]
    return value


def load_corrections(path: Path) -> dict[str, str | None]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = csv.DictReader(file)
        required = {"혜택ID", "가맹점목록"}
        if not rows.fieldnames or not required.issubset(rows.fieldnames):
            raise ValueError(f"required CSV columns are missing: {sorted(required)}")
        return {
            str(row["혜택ID"]).strip(): nullify(row.get("가맹점목록"))
            for row in rows
            if str(row.get("혜택ID") or "").strip()
        }


def load_aliases(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--alias-csv", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    corrections = load_corrections(args.csv_path)
    with SessionLocal() as db:
        benefits = list(
            db.scalars(
                select(CardBenefit).where(
                    CardBenefit.source_benefit_id.in_(corrections)
                )
            ).all()
        )
        merchant_changes: list[tuple[str, Any, Any]] = []
        nan_field_changes = 0
        nested_json_changes = 0

        for benefit in benefits:
            source_id = str(benefit.source_benefit_id)
            new_merchant = corrections[source_id]
            conditions = nullify(dict(benefit.additional_conditions or {}))
            raw_data = nullify(dict(benefit.raw_data or {}))
            if conditions != (benefit.additional_conditions or {}):
                nested_json_changes += 1
            if raw_data != (benefit.raw_data or {}):
                nested_json_changes += 1
            old_merchant = conditions.get("merchant_list")

            if old_merchant != new_merchant:
                merchant_changes.append((source_id, old_merchant, new_merchant))
                conditions["merchant_list"] = new_merchant
            if "가맹점목록" in raw_data:
                raw_data["가맹점목록"] = new_merchant
            if "merchant_list" in raw_data:
                raw_data["merchant_list"] = new_merchant

            if conditions != benefit.additional_conditions:
                benefit.additional_conditions = conditions
            if raw_data != benefit.raw_data:
                benefit.raw_data = raw_data

            for field in TEXT_FIELDS:
                old_value = getattr(benefit, field)
                new_value = nullify(old_value)
                if old_value != new_value:
                    setattr(benefit, field, new_value)
                    nan_field_changes += 1

        missing = set(corrections) - {
            str(benefit.source_benefit_id) for benefit in benefits
        }
        alias_inserts = 0
        alias_updates = 0
        if args.alias_csv:
            alias_rows = load_aliases(args.alias_csv)
            existing_aliases = {
                row.alias: row
                for row in db.scalars(select(MerchantAlias)).all()
            }
            for row in alias_rows:
                alias = nullify(row.get("alias"))
                canonical = nullify(row.get("canonical_merchant"))
                category = nullify(row.get("category"))
                if not alias or not canonical or not category:
                    continue
                values = {
                    "canonical_merchant": canonical,
                    "category": category,
                    "report_category": category,
                    "match_type": nullify(row.get("match_type")),
                    "priority": int(row["priority"]) if row.get("priority") else None,
                    "source": nullify(row.get("source")),
                }
                existing = existing_aliases.get(alias)
                if existing is None:
                    existing = MerchantAlias(alias=alias, **values)
                    db.add(existing)
                    existing_aliases[alias] = existing
                    alias_inserts += 1
                # Existing aliases may contain production-only report-category
                # corrections. Preserve them; the handoff only fills gaps.
        print(f"handoff_rows={len(corrections)} db_rows={len(benefits)}")
        print(
            f"merchant_changes={len(merchant_changes)} "
            f"nan_field_changes={nan_field_changes} "
            f"nested_json_changes={nested_json_changes}"
        )
        print(f"missing_source_ids={len(missing)}")
        print(f"alias_inserts={alias_inserts} alias_updates={alias_updates}")
        for source_id, before, after in merchant_changes[:25]:
            print(f"  {source_id}: {before!r} -> {after!r}")

        if args.apply:
            db.commit()
            print("applied=true")
        else:
            db.rollback()
            print("applied=false (dry-run)")


if __name__ == "__main__":
    main()
