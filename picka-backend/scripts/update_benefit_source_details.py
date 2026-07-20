import csv
from pathlib import Path

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.card_benefit import CardBenefit


CSV_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "card_benefits_final.csv"
)


def clean_text(value: str | None) -> str | None:
    if value is None:
        return None

    value = value.strip()

    if not value or value.lower() == "nan":
        return None

    return value


def update_source_details() -> None:
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            "혜택 CSV 파일을 찾을 수 없습니다.\n"
            f"확인한 경로: {CSV_PATH}\n"
            "CSV를 이 경로에 넣거나 CSV_PATH를 실제 파일명에 맞게 "
            "수정해 주세요."
        )

    db = SessionLocal()

    updated_count = 0
    not_found_count = 0
    empty_detail_count = 0
    invalid_id_count = 0

    try:
        detail_by_id: dict[str, str] = {}

        with CSV_PATH.open(
            mode="r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            reader = csv.DictReader(file)

            if reader.fieldnames is None:
                raise ValueError("CSV 헤더를 읽을 수 없습니다.")

            required_columns = {"혜택ID", "상세"}
            missing_columns = required_columns.difference(reader.fieldnames)

            if missing_columns:
                raise ValueError(
                    "CSV 필수 컬럼이 없습니다: "
                    + ", ".join(sorted(missing_columns))
                )

            for row in reader:
                source_benefit_id = clean_text(row.get("혜택ID"))
                source_detail = clean_text(row.get("상세"))

                if not source_benefit_id:
                    invalid_id_count += 1
                    continue

                if not source_detail:
                    empty_detail_count += 1
                    continue

                detail_by_id[source_benefit_id] = source_detail

        benefits = db.scalars(
            select(CardBenefit).where(
                CardBenefit.source_benefit_id.in_(detail_by_id)
            )
        ).all()

        benefit_by_id = {
            benefit.source_benefit_id: benefit
            for benefit in benefits
        }

        for source_benefit_id, source_detail in detail_by_id.items():
            benefit = benefit_by_id.get(source_benefit_id)

            if benefit is None:
                not_found_count += 1
                continue

            benefit.source_detail = source_detail
            updated_count += 1

        db.commit()

        print("\n업데이트 완료")
        print(f"업데이트: {updated_count}")
        print(f"DB에서 못 찾음: {not_found_count}")
        print(f"상세 내용 없음: {empty_detail_count}")
        print(f"혜택ID 없음: {invalid_id_count}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    update_source_details()
