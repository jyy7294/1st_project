from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionLocal
from app.models.card import Card

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

    if not cards:
        print("카드 데이터가 없습니다.")
        return

    if not isinstance(all_benefits, list):
        raise ValueError(
            "'benefits' 데이터가 list 형태가 아닙니다."
        )

    # 우선 첫 번째 카드 한 장만 테스트
    first_card_data = cards[0]
    source_card_id = first_card_data.get("카드번호")

    # 카드번호가 같은 혜택만 추출
    benefit_data_list = [
        benefit
        for benefit in all_benefits
        if isinstance(benefit, dict)
        and benefit.get("카드번호") == source_card_id
    ]

    db = SessionLocal()

    try:
        # 이미 같은 카드가 저장되어 있는지 확인
        existing_card = db.scalar(
            select(Card).where(
                Card.source_card_id == source_card_id
            )
        )

        if existing_card:
            print(
                "이미 저장된 카드입니다:",
                existing_card.card_name,
            )
            return

        # JSON 카드 데이터 → Card ORM 객체
        card_model = create_card_model(
            first_card_data
        )

        db.add(card_model)

        # INSERT 후 DB 기본키 card_model.id를 받기 위해 flush
        db.flush()

        print("생성된 DB 카드 ID:", card_model.id)

        # JSON 혜택 데이터 → CardBenefit ORM 객체들
        benefit_models = create_benefit_models(
            benefit_data_list
        )

        # 각 혜택을 현재 카드와 연결
        for benefit_model in benefit_models:
            benefit_model.card_id = card_model.id

        db.add_all(benefit_models)

        # 실제 DB 반영
        db.commit()

        print("\nDB 저장 성공")
        print("- 카드명:", card_model.card_name)
        print("- 원본 카드번호:", card_model.source_card_id)
        print("- DB 카드 ID:", card_model.id)
        print("- 저장한 혜택 수:", len(benefit_models))

    except SQLAlchemyError as error:
        db.rollback()

        print("\nDB 저장 실패")
        print("오류 내용:")
        print(error)

        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()