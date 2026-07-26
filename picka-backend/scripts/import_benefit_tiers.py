from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.database import SessionLocal
from app.models.benefit_tier import BenefitTier
from app.models.card_benefit import CardBenefit

from scripts.import_cards import (
    JSON_PATH,
    clean_nested_value,
    clean_value,
    load_json,
)


def create_tier_model(card_benefit_id: int, tier_data: dict) -> BenefitTier:
    return BenefitTier(
        card_benefit_id=card_benefit_id,
        source_benefit_id=str(
            clean_value(
                tier_data.get("혜택ID")
            )
        ),
        tier_order=clean_value(
            tier_data.get("구간순번")
        ),
        required_spending=clean_value(
            tier_data.get("실적조건")
        ),
        monthly_limit=clean_value(
            tier_data.get("월한도")
        ),
        benefit_value=clean_value(
            tier_data.get("혜택값")
        ),
        benefit_unit=clean_value(
            tier_data.get("혜택단위")
        ),
        extraction_method=clean_value(
            tier_data.get("구간추출방식")
        ),
        review_required=clean_value(
            tier_data.get("구간검수필요")
        ),
        raw_data=clean_nested_value(
            tier_data
        ),
    )


def main():
    data = load_json(JSON_PATH)

    tiers = data.get("benefit_tiers", [])

    print(f"전체 benefit_tiers : {len(tiers)}")

    db = SessionLocal()

    inserted = 0
    skipped = 0

    try:

        for index, tier in enumerate(tiers, start=1):

            source_benefit_id = str(
                tier.get("혜택ID")
            )

            card_benefit = db.scalar(
                select(CardBenefit).where(
                    CardBenefit.source_benefit_id
                    == source_benefit_id
                )
            )

            if card_benefit is None:
                skipped += 1
                continue

            exists = db.scalar(
                select(BenefitTier).where(
                    BenefitTier.card_benefit_id
                    == card_benefit.id,
                    BenefitTier.tier_order
                    == clean_value(
                        tier.get("구간순번")
                    ),
                )
            )

            if exists:
                skipped += 1
                continue

            model = create_tier_model(
                card_benefit.id,
                tier,
            )

            db.add(model)

            inserted += 1

            if index % 500 == 0:
                db.commit()

                print(
                    f"[{index}/{len(tiers)}] "
                    f"저장:{inserted} "
                    f"건너뜀:{skipped}"
                )

        db.commit()

        print("\n===== 완료 =====")
        print("저장 :", inserted)
        print("건너뜀 :", skipped)

    except SQLAlchemyError as e:

        db.rollback()

        print(e)

        raise

    finally:

        db.close()


if __name__ == "__main__":
    main()
