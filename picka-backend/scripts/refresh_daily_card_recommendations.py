"""한국시간 매일 00시에 실행할 신규 카드 추천 캐시 갱신 작업."""

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import User
from app.services.spending_pattern_recommendation_service import (
    get_daily_card_recommendations,
)


def main() -> None:
    with SessionLocal() as db:
        user_ids = db.scalars(select(User.id)).all()
        for user_id in user_ids:
            get_daily_card_recommendations(
                db,
                user_id=user_id,
                card_type="credit",
                limit=3,
                force_refresh=True,
            )
        print(f"refreshed daily card recommendations for {len(user_ids)} users")


if __name__ == "__main__":
    main()
