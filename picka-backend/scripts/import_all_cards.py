from collections import defaultdict

from sqlalchemy import delete, select
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionLocal
from app.models.card import Card
from app.models.card_benefit import CardBenefit

from scripts.import_cards import (
    JSON_PATH,
    create_benefit_models,
    create_card_model,
    extract_cards,
    load_json,
)


def main() -> None:
    data = load_json(JSON_PATH)

    cards = extract_cards(data)
    all_benefits = data.get("benefits", [])

    if not isinstance(all_benefits, list):
        raise ValueError("'benefits' 데이터가 list 형태가 아닙니다.")

    print(f"전체 카드 개수: {len(cards)}")
    print(f"전체 혜택 개수: {len(all_benefits)}")

    # 카드번호별로 혜택을 미리 묶어둔다.
    benefits_by_card_id: dict[int, list[dict]] = defaultdict(list)

    for benefit_data in all_benefits:
        if not isinstance(benefit_data, dict):
            continue

        source_card_id = benefit_data.get("카드번호")

        if source_card_id is not None:
            benefits_by_card_id[source_card_id].append(benefit_data)

    db = SessionLocal()

    inserted_card_count = 0
    inserted_benefit_count = 0
    skipped_card_count = 0

    try:
        for index, card_data in enumerate(cards, start=1):
            source_card_id = card_data.get("카드번호")

            if source_card_id is None:
                print(f"[건너뜀] 카드번호 없음: {card_data.get('카드명')}")
                skipped_card_count += 1
                continue

            # 이미 저장된 카드인지 확인
            existing_card = db.scalar(
                select(Card).where(
                    Card.source_card_id == source_card_id
                )
            )

            if existing_card:
                skipped_card_count += 1

                if index % 100 == 0:
                    print(
                        f"[{index}/{len(cards)}] 진행 중 "
                        f"- 기존 카드 건너뜀: {existing_card.card_name}"
                    )

                continue

            card_model = create_card_model(card_data)

            db.add(card_model)
            db.flush()

            benefit_data_list = benefits_by_card_id.get(
                source_card_id,
                [],
            )

            benefit_models = create_benefit_models(
                benefit_data_list
            )

            for benefit_model in benefit_models:
                benefit_model.card_id = card_model.id

            if benefit_models:
                db.add_all(benefit_models)

            inserted_card_count += 1
            inserted_benefit_count += len(benefit_models)

            # 100장마다 중간 저장
            if index % 100 == 0:
                db.commit()

                print(
                    f"[{index}/{len(cards)}] 중간 저장 완료 "
                    f"- 카드: {inserted_card_count}개 "
                    f"- 혜택: {inserted_benefit_count}개 "
                    f"- 건너뜀: {skipped_card_count}개"
                )

        # 마지막 남은 데이터 저장
        db.commit()

        print("\n전체 DB 적재 완료")
        print(f"- 새로 저장한 카드 수: {inserted_card_count}")
        print(f"- 새로 저장한 혜택 수: {inserted_benefit_count}")
        print(f"- 기존 또는 오류로 건너뛴 카드 수: {skipped_card_count}")

    except SQLAlchemyError as error:
        db.rollback()

        print("\n전체 DB 적재 실패")
        print("오류 내용:")
        print(error)

        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()