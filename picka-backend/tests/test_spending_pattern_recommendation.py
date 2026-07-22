import unittest
from datetime import date, datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models import Card, CardBenefit, Transaction, User, UserCard
from app.services.spending_pattern_recommendation_service import (
    build_monthly_spending_profile,
    normalize_spending_category,
    recommend_new_cards_by_spending,
)


class SpendingPatternRecommendationTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self._seed()

        def override_get_db():
            with self.Session() as db:
                yield db

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def _seed(self):
        with self.Session() as db:
            db.add(User(id=1, email="pattern@example.com", name="패턴 사용자"))
            cards = [
                Card(id=1, card_name="보유 카드", card_type="신용", is_active=True),
                Card(
                    id=2,
                    card_name="마트 특화 카드",
                    issuer="A카드",
                    card_type="신용",
                    annual_fee=10_000,
                    previous_spending=0,
                    is_active=True,
                ),
                Card(
                    id=3,
                    card_name="낮은 혜택 카드",
                    issuer="B카드",
                    card_type="credit",
                    annual_fee=0,
                    previous_spending=0,
                    is_active=True,
                ),
                Card(id=4, card_name="체크 카드", card_type="체크", is_active=True),
            ]
            db.add_all(cards)
            db.flush()
            db.add_all([
                CardBenefit(
                    card_id=2,
                    source_benefit_id="2-1",
                    benefit_name="마트 10% 할인",
                    category="마트/쇼핑",
                    benefit_type="할인",
                    benefit_unit="%",
                    benefit_value=10,
                    monthly_benefit_limit=10_000,
                    additional_conditions={"scoring_grade": "A_확정계산"},
                ),
                CardBenefit(
                    card_id=3,
                    source_benefit_id="3-1",
                    benefit_name="마트 5% 할인",
                    category="마트/쇼핑",
                    benefit_type="할인",
                    benefit_unit="%",
                    benefit_value=5,
                    additional_conditions={"scoring_grade": "A_확정계산"},
                ),
                CardBenefit(
                    card_id=4,
                    source_benefit_id="4-1",
                    benefit_name="마트 체크 할인",
                    category="마트/쇼핑",
                    benefit_type="할인",
                    benefit_unit="%",
                    benefit_value=20,
                    additional_conditions={"scoring_grade": "A_확정계산"},
                ),
            ])
            owned = UserCard(user_id=1, card_id=1, is_active=True)
            db.add(owned)
            db.flush()
            for index, (month, amount) in enumerate(
                [("2026-05", 100_000), ("2026-06", 200_000)], start=1
            ):
                db.add(Transaction(
                    user_id=1,
                    user_card_id=owned.id,
                    card_id=1,
                    merchant_name="테스트 마트",
                    payment_category="MART",
                    original_payment_amount=amount,
                    saved_amount=0,
                    final_approved_amount=amount,
                    approval_number=f"PATTERN-{index}",
                    status="APPROVED",
                    usage_month=month,
                    approved_at=datetime(2026, 5 + index - 1, 1, tzinfo=timezone.utc),
                ))
            db.commit()

    def test_category_normalization(self):
        self.assertEqual(normalize_spending_category("DELIVERY"), "배달앱")
        self.assertEqual(normalize_spending_category("MART"), "마트/쇼핑")
        self.assertEqual(normalize_spending_category("TUITION"), "교육/육아")

    def test_profile_uses_latest_months_and_monthly_average(self):
        with self.Session() as db:
            profile = build_monthly_spending_profile(db, 1)
        self.assertEqual(profile, {"마트/쇼핑": 150_000})

    def test_recommends_only_unowned_cards_of_requested_type(self):
        with self.Session() as db:
            result = recommend_new_cards_by_spending(
                db,
                user_id=1,
                card_type="credit",
                limit=3,
                reference_date=date(2026, 6, 8),
            )

        self.assertEqual([card["id"] for card in result["cards"]], [3, 2])
        self.assertEqual(result["cards"][0]["benefitName"], "마트 5% 할인")
        self.assertEqual(result["cards"][0]["total"], 120_000)
        self.assertEqual(result["cards"][0]["fee"], 0)
        self.assertEqual(result["cards"][1]["total"], 110_000)
        self.assertEqual(result["analysisStartDate"], "2026-06-01")
        self.assertEqual(result["analysisEndDate"], "2026-06-07")
        self.assertEqual(result["updateCycle"], "daily 00:00 Asia/Seoul")
        self.assertEqual(result["topCategory"], "마트/쇼핑")
        self.assertEqual(result["topCategorySpend"], 200_000)
        self.assertIn("최근 7일간 마트/쇼핑", result["cards"][0]["recommendationMessage"])

    def test_api_contract_and_query_validation(self):
        response = self.client.get(
            "/api/v1/users/1/card-recommendations",
            params={"type": "credit", "limit": 1},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["cached"])
        self.assertEqual(len(response.json()["cards"]), 1)
        self.assertEqual(
            set(response.json()["cards"][0]),
            {
                "id", "name", "issuer", "benefitName", "rate", "total",
                "fee", "url", "image_url", "benefitCategory", "monthlySpend",
                "recommendationMessage", "matchedMerchants",
            },
        )
        self.assertEqual(
            self.client.get(
                "/api/v1/users/1/card-recommendations",
                params={"type": "invalid"},
            ).status_code,
            422,
        )
        self.assertEqual(
            self.client.get(
                "/api/v1/users/999/card-recommendations"
            ).status_code,
            404,
        )
        cached_response = self.client.get(
            "/api/v1/users/1/card-recommendations",
            params={"type": "credit", "limit": 1},
        )
        self.assertTrue(cached_response.json()["cached"])
        self.assertEqual(
            cached_response.json()["generatedAt"],
            response.json()["generatedAt"],
        )

    def test_specific_merchant_benefit_is_found_outside_transaction_category(self):
        with self.Session() as db:
            card = Card(
                id=5,
                card_name="특정 마트 카드",
                issuer="C카드",
                card_type="신용카드",
                annual_fee=0,
                previous_spending=0,
                is_active=True,
            )
            db.add(card)
            db.flush()
            db.add(CardBenefit(
                card_id=5,
                source_benefit_id="5-1",
                benefit_name="테스트 마트 20% 할인",
                category="생활",
                benefit_type="할인",
                benefit_unit="%",
                benefit_value=20,
                additional_conditions={"scoring_grade": "A_확정계산"},
            ))
            db.commit()

            result = recommend_new_cards_by_spending(
                db,
                user_id=1,
                card_type="credit",
                limit=3,
                reference_date=date(2026, 6, 8),
            )

        specific = next(card for card in result["cards"] if card["id"] == 5)
        self.assertIn("테스트 마트", specific["matchedMerchants"])
        self.assertEqual(specific["benefitName"], "테스트 마트 20% 할인")


if __name__ == "__main__":
    unittest.main()
from fastapi.testclient import TestClient
