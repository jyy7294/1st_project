from sqlalchemy import delete, select

from app.core.database import SessionLocal
from app.models.benefit_usage import BenefitUsage
from app.models.card import Card
from app.models.monthly_card_usage import MonthlyCardUsage
from app.models.user import User
from app.models.user_card import UserCard


SEED_EMAIL = "test@example.com"
SEED_MONTH = "2026-07"
SEED_CARD_IDS = (53, 78, 423)


def seed_user_state() -> None:
    db = SessionLocal()
    created = {
        "users": 0,
        "user_cards": 0,
        "monthly_card_usage": 0,
        "benefit_usage": 0,
    }

    try:
        user = db.scalar(select(User).where(User.email == SEED_EMAIL))
        if user is None:
            user = User(
                email=SEED_EMAIL,
                name="테스트유저",
            )
            db.add(user)
            db.flush()
            created["users"] += 1

        cards = db.scalars(
            select(Card)
            .where(Card.id.in_(SEED_CARD_IDS))
            .order_by(Card.id)
        ).all()
        if len(cards) != len(SEED_CARD_IDS):
            found_ids = {card.id for card in cards}
            missing_ids = sorted(set(SEED_CARD_IDS) - found_ids)
            raise RuntimeError(f"Seed 카드가 DB에 없습니다: {missing_ids}")

        card_ids = [card.id for card in cards]

        # 이 사용자와 Seed 월에 속한 기존 데모 상태만 정리합니다.
        db.execute(
            delete(BenefitUsage).where(
                BenefitUsage.user_id == user.id,
                BenefitUsage.usage_month == SEED_MONTH,
                BenefitUsage.card_id.not_in(card_ids),
            )
        )
        db.execute(
            delete(MonthlyCardUsage).where(
                MonthlyCardUsage.user_id == user.id,
                MonthlyCardUsage.usage_month == SEED_MONTH,
                MonthlyCardUsage.card_id.not_in(card_ids),
            )
        )
        db.execute(
            delete(UserCard).where(
                UserCard.user_id == user.id,
                UserCard.card_id.not_in(card_ids),
            )
        )

        for index, card in enumerate(cards, start=1):
            user_card = db.scalar(
                select(UserCard).where(
                    UserCard.user_id == user.id,
                    UserCard.card_id == card.id,
                )
            )
            if user_card is None:
                user_card = UserCard(
                    user_id=user.id,
                    card_id=card.id,
                    nickname=f"데모 카드 {index}",
                    is_active=True,
                )
                db.add(user_card)
                created["user_cards"] += 1
            else:
                user_card.is_active = True

            monthly_usage = db.scalar(
                select(MonthlyCardUsage).where(
                    MonthlyCardUsage.user_id == user.id,
                    MonthlyCardUsage.card_id == card.id,
                    MonthlyCardUsage.usage_month == SEED_MONTH,
                )
            )
            if monthly_usage is None:
                monthly_usage = MonthlyCardUsage(
                    user_id=user.id,
                    card_id=card.id,
                    usage_month=SEED_MONTH,
                )
                db.add(monthly_usage)
                created["monthly_card_usage"] += 1

            monthly_usage.previous_month_spending = 600_000
            monthly_usage.current_month_spending = 150_000
            monthly_usage.card_monthly_benefit_used = 0

        # 데모 추천을 방해하지 않도록 새 카드도 혜택 사용량 0(행 없음)으로 시작합니다.
        db.execute(
            delete(BenefitUsage).where(
                BenefitUsage.user_id == user.id,
                BenefitUsage.usage_month == SEED_MONTH,
                BenefitUsage.card_id.in_(card_ids),
            )
        )

        db.commit()

        print("사용자 상태 Seed 완료")
        print(f"- 사용자: {user.email} (id={user.id})")
        print(f"- 보유 카드 ID: {card_ids}")
        print(f"- 사용 월: {SEED_MONTH}")
        print("- 전월실적: 600,000원")
        print("- 당월 사용액: 150,000원")
        print("- 카드 월 혜택 사용액: 0원")
        print(f"- 이번 실행 생성 건수: {created}")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_user_state()
