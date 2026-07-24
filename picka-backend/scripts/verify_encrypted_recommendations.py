from datetime import date

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import User
from app.services.spending_pattern_recommendation_service import (
    recommend_new_cards_by_spending,
)


def main() -> None:
    with SessionLocal() as db:
        user_ids = db.scalars(select(User.id).order_by(User.id)).all()
        results = []
        for user_id in user_ids:
            for card_type in ("credit", "check"):
                result = recommend_new_cards_by_spending(
                    db,
                    user_id=user_id,
                    card_type=card_type,
                    limit=3,
                    reference_date=date.today(),
                )
                results.append({
                    "user_id": user_id,
                    "card_type": card_type,
                    "recommended": len(result["cards"]),
                    "excluded": len(result["excludedCards"]),
                })
        print(results)


if __name__ == "__main__":
    main()
