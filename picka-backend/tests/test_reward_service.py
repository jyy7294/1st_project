import unittest

from app.services.reward_service import calculate_transaction_rewards


class RewardServiceTest(unittest.TestCase):
    def card(self, benefit: dict) -> dict:
        return {
            "card_company": "테스트카드",
            "previous_month_spending": 500_000,
            "benefits": [benefit],
        }

    def test_percentage_point_reward(self):
        rewards = calculate_transaction_rewards(
            self.card({
                "card_benefit_id": 1,
                "benefit_name": "마이신한포인트 5% 적립",
                "category": "카페/디저트",
                "benefit_type": "포인트 적립",
                "benefit_unit": "%",
                "benefit_value": 5,
                "additional_conditions": {"scoring_grade": "A_확정계산"},
            }),
            payment_category="카페",
            payment_amount=10_000,
        )
        self.assertEqual(rewards[0]["reward_amount"], 500)
        self.assertEqual(rewards[0]["reward_program"], "마이신한포인트")
        self.assertEqual(rewards[0]["reward_unit"], "P")

    def test_mileage_uses_text_denominator(self):
        rewards = calculate_transaction_rewards(
            self.card({
                "card_benefit_id": 2,
                "benefit_name": "2천원당 대한항공 1마일리지 적립",
                "category": "모든가맹점",
                "benefit_type": "마일리지 적립",
                "benefit_unit": "마일/천원",
                "benefit_value": 1,
                "additional_conditions": {"scoring_grade": "A_확정계산"},
            }),
            payment_category="편의점",
            payment_amount=10_000,
        )
        self.assertEqual(rewards[0]["reward_amount"], 5)
        self.assertEqual(rewards[0]["reward_program"], "스카이패스")
        self.assertEqual(rewards[0]["reward_unit"], "mile")

    def test_unknown_rate_is_not_guessed(self):
        rewards = calculate_transaction_rewards(
            self.card({
                "benefit_name": "포인트 적립 제공",
                "category": "모든가맹점",
                "benefit_type": "포인트 적립",
                "benefit_unit": None,
                "benefit_value": None,
                "additional_conditions": {"scoring_grade": "A_확정계산"},
            }),
            payment_category="편의점",
            payment_amount=10_000,
        )
        self.assertEqual(rewards, [])


if __name__ == "__main__":
    unittest.main()
