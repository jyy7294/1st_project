import unittest

from app.services.recommendation_service import calculate_card_benefit


def make_card(rule: str) -> dict:
    return {
        "card_id": 1,
        "card_name": "테스트 카드",
        "card_company": "테스트 카드사",
        "card_image": None,
        "previous_month_spending": 1_000_000,
        "required_spending": 0,
        "monthly_benefit_used": 0,
        "monthly_total_limit": None,
        "benefit_usage": {},
        "benefits": [{
            "혜택ID": "benefit-1",
            "카테고리": "편의점",
            "혜택유형": "할인",
            "혜택값": 10,
            "혜택단위": "%",
            "실적조건": None,
            "스코어링등급": "A_확정계산",
            "요약": rule,
        }],
    }


class ConditionalBenefitTest(unittest.TestCase):
    def calculate(self, rule: str) -> dict:
        return calculate_card_benefit(
            make_card(rule),
            merchant_name="테스트 편의점",
            payment_category="편의점",
            payment_amount=50_000,
        )

    def test_item_exception_keeps_confirmed_benefit_with_caveat(self):
        result = self.calculate("편의점 10% 할인, 상품권 구매 제외")

        self.assertEqual(result["expected_benefit"], 5_000)
        self.assertFalse(result["is_conditional"])
        self.assertIsNotNone(result["caveat"])

    def test_ambiguous_merchant_scope_is_conditional(self):
        result = self.calculate("편의점 10% 할인, 일부 입점 매장 제외")

        self.assertEqual(result["expected_benefit"], 5_000)
        self.assertTrue(result["eligible"])
        self.assertTrue(result["is_conditional"])
        self.assertIn("확인", result["caveat"])

    def test_clear_rule_is_confirmed_without_caveat(self):
        result = self.calculate("편의점 10% 할인")

        self.assertEqual(result["expected_benefit"], 5_000)
        self.assertFalse(result["is_conditional"])
        self.assertIsNone(result["caveat"])

    def test_ambiguous_scope_uses_deterministic_caveat(self):
        result = self.calculate("편의점 10% 할인, 일부 매장만 적용")
        self.assertEqual(result["expected_benefit"], 5_000)
        self.assertTrue(result["is_conditional"])
        self.assertIn("지정·제휴 가맹점", result["caveat"])


if __name__ == "__main__":
    unittest.main()
