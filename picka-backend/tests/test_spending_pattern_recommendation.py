import unittest
from datetime import date, datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.models import (
    Card,
    CardBenefit,
    CardBenefitEligibilityRule,
    CardEligibilityRule,
    Transaction,
    User,
    UserCard,
    UserEligibility,
    RecommendationAuditLog,
)
from app.services.spending_pattern_recommendation_service import (
    RECOMMENDATION_POLICY_VERSION,
    build_monthly_spending_profile,
    build_recent_spending_profile,
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
        self.assertEqual(normalize_spending_category("FOOD_DINING"), "푸드/외식")
        self.assertEqual(normalize_spending_category("FUEL"), "주유")
        self.assertEqual(
            normalize_spending_category("AIRLINE_MILEAGE"),
            "항공/마일리지",
        )

    def test_profile_uses_latest_months_and_monthly_average(self):
        with self.Session() as db:
            profile = build_monthly_spending_profile(db, 1)
        self.assertEqual(profile, {"마트/쇼핑": 150_000})

    def test_frequency_wins_unless_counts_are_similar(self):
        with self.Session() as db:
            owned = db.query(UserCard).filter_by(user_id=1, card_id=1).one()
            db.add_all([
                Transaction(
                    user_id=1, user_card_id=owned.id, card_id=1,
                    merchant_name="올리브영", payment_category="BEAUTY",
                    original_payment_amount=500_000, saved_amount=0,
                    final_approved_amount=500_000, approval_number="EWMA-OLD",
                    status="APPROVED", usage_month="2026-05",
                    approved_at=datetime(2026, 5, 10, tzinfo=timezone.utc),
                ),
                Transaction(
                    user_id=1, user_card_id=owned.id, card_id=1,
                    merchant_name="CGV", payment_category="MOVIE",
                    original_payment_amount=100_000, saved_amount=0,
                    final_approved_amount=100_000, approval_number="EWMA-NEW",
                    status="APPROVED", usage_month="2026-06",
                    approved_at=datetime(2026, 6, 7, tzinfo=timezone.utc),
                ),
                *[
                    Transaction(
                        user_id=1, user_card_id=owned.id, card_id=1,
                        merchant_name="CGV", payment_category="MOVIE",
                        original_payment_amount=100_000, saved_amount=0,
                        final_approved_amount=100_000,
                        approval_number=f"FREQ-{index}", status="APPROVED",
                        usage_month="2026-06",
                        approved_at=datetime(2026, 6, 7, tzinfo=timezone.utc),
                    )
                    for index in range(3)
                ],
            ])
            db.commit()
            _, _, profile, _, primary = build_recent_spending_profile(
                db, 1, reference_date=date(2026, 6, 8)
            )

        self.assertLess(profile["영화/문화"], profile["뷰티/피트니스"])
        self.assertEqual(primary, "영화/문화")

    def test_recommends_only_unowned_cards_of_requested_type(self):
        with self.Session() as db:
            result = recommend_new_cards_by_spending(
                db,
                user_id=1,
                card_type="credit",
                limit=3,
                reference_date=date(2026, 6, 8),
            )

        self.assertEqual([card["id"] for card in result["cards"]], [2, 3])
        self.assertEqual(result["cards"][0]["benefitName"], "마트 10% 할인")
        self.assertEqual(result["cards"][0]["total"], 110_000)
        self.assertEqual(result["cards"][0]["fee"], 10_000)
        self.assertEqual(result["cards"][1]["total"], 78_000)
        self.assertEqual(result["analysisStartDate"], "2026-03-10")
        self.assertEqual(result["analysisEndDate"], "2026-06-07")
        self.assertEqual(
            result["updateCycle"],
            "daily 00:00 Asia/Seoul · rolling 30d 50%/30d 30%/30d 20%",
        )
        self.assertEqual(result["topCategory"], "마트/쇼핑")
        self.assertEqual(result["topCategorySpend"], 130_000)
        self.assertIn("최근 3개월 소비에서 마트/쇼핑", result["cards"][0]["recommendationMessage"])
        benefit = result["cards"][0]["benefits"][0]
        self.assertEqual(benefit["category"], "마트/쇼핑")
        self.assertEqual(benefit["value"], 10)
        self.assertEqual(benefit["unit"], "%")
        self.assertEqual(benefit["monthlyLimit"], 10_000)

    def test_excludes_military_service_cards_for_non_military_personas(self):
        with self.Session() as db:
            db.add(Card(
                id=6,
                card_name="IBK 나라사랑카드",
                issuer="IBK기업은행",
                card_type="체크카드",
                is_active=True,
            ))
            db.add(CardEligibilityRule(
                card_id=6,
                eligibility_type="MILITARY_SERVICE",
                required_value="true",
                comparison_operator="EQ",
            ))
            db.add(UserEligibility(
                user_id=1,
                eligibility_type="MILITARY_SERVICE",
                eligibility_value="false",
                verification_status="SELF_REPORTED",
            ))
            db.commit()

            result = recommend_new_cards_by_spending(
                db,
                user_id=1,
                card_type="check",
                limit=20,
                reference_date=date(2026, 6, 8),
            )

        self.assertNotIn(
            "IBK 나라사랑카드",
            [card["name"] for card in result["cards"]],
        )
        excluded = next(
            card
            for card in result["excludedCards"]
            if card["cardName"] == "IBK 나라사랑카드"
        )
        self.assertEqual(excluded["status"], "EXCLUDED")
        self.assertEqual(excluded["eligibilityType"], "MILITARY_SERVICE")

    def test_child_count_rule_requires_at_least_two_children(self):
        with self.Session() as db:
            db.add(Card(
                id=8,
                card_name="다둥이 행복카드",
                card_type="신용카드",
                is_active=True,
            ))
            db.add(CardEligibilityRule(
                card_id=8,
                eligibility_type="CHILDREN_COUNT",
                required_value="2",
                comparison_operator="GTE",
            ))
            db.add(UserEligibility(
                user_id=1,
                eligibility_type="CHILDREN_COUNT",
                eligibility_value="1",
                verification_status="VERIFIED",
            ))
            db.commit()

            result = recommend_new_cards_by_spending(
                db, user_id=1, card_type="credit", limit=20,
                reference_date=date(2026, 6, 8),
            )

        self.assertNotIn(8, [card["id"] for card in result["cards"]])
        excluded = next(card for card in result["excludedCards"] if card["cardId"] == 8)
        self.assertEqual(excluded["eligibilityType"], "CHILDREN_COUNT")

    def test_api_contract_and_query_validation(self):
        response = self.client.get(
            "/api/v1/users/1/card-recommendations",
            params={"type": "credit", "limit": 1},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["cached"])
        self.assertEqual(len(response.json()["cards"]), 1)
        with self.Session() as db:
            audit = db.scalar(select(RecommendationAuditLog))
            self.assertEqual(audit.request_kind, "NEW_CARD_SPENDING_PATTERN")
            self.assertFalse(audit.cache_hit)
            self.assertEqual(audit.policy_version, RECOMMENDATION_POLICY_VERSION)
        self.assertEqual(
            set(response.json()["cards"][0]),
            {
                "id", "name", "issuer", "benefitName", "rate", "total",
                "benefitValue", "benefitUnit", "expectedBenefitAmount",
                "fee", "url", "image_url", "benefitCategory", "monthlySpend",
                "recommendationMessage", "matchedMerchants",
                "benefits",
            },
        )
        self.assertEqual(
            response.json()["policyVersion"],
            RECOMMENDATION_POLICY_VERSION,
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
        refreshed_response = self.client.get(
            "/api/v1/users/1/card-recommendations",
            params={"type": "credit", "limit": 1, "refresh": True},
        )
        self.assertFalse(refreshed_response.json()["cached"])

    def test_fixed_amount_benefit_exposes_won_unit_not_percent(self):
        with self.Session() as db:
            db.add(Card(
                id=9,
                card_name="고정금액 할인 카드",
                card_type="신용카드",
                annual_fee=0,
                is_active=True,
            ))
            db.flush()
            db.add(CardBenefit(
                card_id=9,
                source_benefit_id="9-1",
                benefit_name="마트 1,000원 할인",
                category="마트/쇼핑",
                benefit_type="할인",
                benefit_unit="원",
                benefit_value=1_000,
                additional_conditions={"scoring_grade": "A_확정계산"},
            ))
            owned = db.query(UserCard).filter_by(user_id=1, card_id=1).one()
            db.add_all([
                Transaction(
                    user_id=1,
                    user_card_id=owned.id,
                    card_id=1,
                    merchant_name=f"추가 마트 {index}",
                    payment_category="MART",
                    original_payment_amount=10_000,
                    saved_amount=0,
                    final_approved_amount=10_000,
                    approval_number=f"FIXED-FREQUENCY-{index}",
                    status="APPROVED",
                    usage_month="2026-06",
                    approved_at=datetime(2026, 6, 7, tzinfo=timezone.utc),
                )
                for index in range(4)
            ])
            db.commit()
            result = recommend_new_cards_by_spending(
                db,
                user_id=1,
                card_type="credit",
                limit=20,
                reference_date=date(2026, 6, 8),
            )

        fixed = next(card for card in result["cards"] if card["id"] == 9)
        self.assertEqual(fixed["benefitValue"], 1_000)
        self.assertEqual(fixed["benefitUnit"], "원")
        self.assertEqual(fixed["rate"], 0)
        self.assertEqual(fixed["expectedBenefitAmount"], 1_000)
        self.assertEqual(fixed["total"], 33_600)

    def test_excludes_unconfirmed_membership_benefit_from_calculation(self):
        with self.Session() as db:
            card = Card(
                id=7,
                card_name="멤버십 전용 혜택 카드",
                card_type="신용",
                is_active=True,
            )
            db.add(card)
            db.flush()
            benefit = CardBenefit(
                card_id=7,
                source_benefit_id="7-1",
                benefit_name="마트 50% 할인",
                category="마트/쇼핑",
                benefit_type="할인",
                benefit_unit="%",
                benefit_value=50,
            )
            db.add(benefit)
            db.flush()
            db.add(CardBenefitEligibilityRule(
                card_benefit_id=benefit.id,
                eligibility_type="MEMBERSHIPS",
                required_value="TEST_MEMBERSHIP",
                comparison_operator="CONTAINS",
                description="테스트 멤버십 가입 필요",
            ))
            db.commit()

            result = recommend_new_cards_by_spending(
                db,
                user_id=1,
                card_type="credit",
                limit=20,
                reference_date=date(2026, 6, 8),
            )

        restricted = next(card for card in result["cards"] if card["id"] == 7)
        self.assertEqual(restricted["total"], 0)
        self.assertGreater(result["excludedBenefitCount"], 0)
        self.assertEqual(
            result["benefitConfirmationRequired"][0]["eligibilityType"],
            "MEMBERSHIPS",
        )

        with self.Session() as db:
            db.add(UserEligibility(
                user_id=1,
                eligibility_type="MEMBERSHIPS",
                eligibility_value="[]",
                verification_status="VERIFIED",
            ))
            db.commit()
            confirmed_result = recommend_new_cards_by_spending(
                db,
                user_id=1,
                card_type="credit",
                limit=20,
                reference_date=date(2026, 6, 8),
            )

        restricted = next(card for card in confirmed_result["cards"] if card["id"] == 7)
        self.assertEqual(restricted["total"], 0)
        self.assertFalse(confirmed_result["benefitConfirmationRequired"])

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
