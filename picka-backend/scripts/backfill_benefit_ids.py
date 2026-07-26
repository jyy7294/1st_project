from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionLocal
from app.models.card_benefit import CardBenefit


def main() -> None:
    db = SessionLocal()

    updated_count = 0
    skipped_count = 0

    try:
        benefits = db.scalars(
            select(CardBenefit)
        ).all()

        print(f"전체 혜택 개수: {len(benefits)}")

        for index, benefit in enumerate(benefits, start=1):
            if benefit.source_benefit_id:
                skipped_count += 1
                continue

            additional_conditions = (
                benefit.additional_conditions
                if isinstance(benefit.additional_conditions, dict)
                else {}
            )

            source_benefit_id = additional_conditions.get(
                "benefit_id"
            )

            # additional_conditions에 없으면 raw_data에서도 확인
            if not source_benefit_id:
                raw_data = (
                    benefit.raw_data
                    if isinstance(benefit.raw_data, dict)
                    else {}
                )

                source_benefit_id = raw_data.get("혜택ID")

            if not source_benefit_id:
                print(
                    f"[확인 필요] 혜택 ID를 찾지 못함: "
                    f"DB ID={benefit.id}, "
                    f"이름={benefit.benefit_name}"
                )
                skipped_count += 1
                continue

            benefit.source_benefit_id = str(source_benefit_id)
            updated_count += 1

            if index % 500 == 0:
                db.commit()

                print(
                    f"[{index}/{len(benefits)}] 중간 저장 "
                    f"- 수정: {updated_count}개"
                )

        db.commit()

        print("\n혜택 ID 채우기 완료")
        print(f"- 수정한 혜택: {updated_count}개")
        print(f"- 건너뛴 혜택: {skipped_count}개")

    except SQLAlchemyError as error:
        db.rollback()
        print("혜택 ID 채우기 실패:")
        print(error)
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()