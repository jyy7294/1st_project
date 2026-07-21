import unittest

from app.services.recommendation_service import calculate_card_benefit


def make_card(benefit: dict, **overrides) -> dict:
    card = {
        "card_id": 1,
        "card_name": "테스트 카드",
        "card_company": "테스트 카드사",
        "card_image": None,
        "previous_month_spending": 1_000_000,
        "required_spending": 0,
        "monthly_benefit_used": 0,
        "monthly_total_limit": None,
        "benefit_usage": {},
        "benefits": [benefit],
    }
    card.update(overrides)
    return card


def make_benefit(scoring_grade: str, **overrides) -> dict:
    benefit = {
        "혜택ID": "test-1",
        "카테고리": "카페",
        "혜택유형": "할인",
        "혜택값": 10,
        "혜택단위": "%",
        "실적조건": None,
        "스코어링등급": scoring_grade,
        "요약": "테스트 혜택",
    }
    benefit.update(overrides)
    return benefit


class ScoringPolicyTest(unittest.TestCase):
    def test_a_grade_confirmed_calculation(self):
        result = calculate_card_benefit(
            make_card(make_benefit("A_확정계산")),
            payment_category="카페",
            payment_amount=10_000,
        )

        self.assertEqual(result["expected_benefit"], 1_000)
        self.assertEqual(result["scoring_grade"], "A_확정계산")
        self.assertFalse(result["is_estimated"])

    def test_b_grade_uses_temporary_monthly_cap(self):
        benefit = make_benefit(
            "B_추정계산",
            혜택값=20,
            임시월캡=3_000,
        )

        result = calculate_card_benefit(
            make_card(benefit),
            payment_category="카페",
            payment_amount=50_000,
        )

        self.assertEqual(result["expected_benefit"], 3_000)
        self.assertEqual(result["applied_cap"], 3_000)
        self.assertTrue(result["is_estimated"])

    def test_b_grade_without_any_cap_returns_zero(self):
        result = calculate_card_benefit(
            make_card(make_benefit("B_추정계산")),
            payment_category="카페",
            payment_amount=50_000,
        )

        self.assertEqual(result["expected_benefit"], 0)
        self.assertTrue(result["is_estimated"])
        self.assertIn(
            "한도 확인 필요",
            result["calculation_reason"],
        )

    def test_c_and_d_grades_are_excluded(self):
        for scoring_grade in ("C_표시전용", "D_제외권장"):
            with self.subTest(scoring_grade=scoring_grade):
                result = calculate_card_benefit(
                    make_card(make_benefit(scoring_grade)),
                    payment_category="카페",
                    payment_amount=10_000,
                )

                self.assertEqual(result["expected_benefit"], 0)
                self.assertFalse(result["eligible"])
                self.assertEqual(
                    result["scoring_grade"],
                    scoring_grade,
                )
                self.assertIn(
                    "계산에서 제외",
                    result["calculation_reason"],
                )

    def test_performance_requirement_is_met(self):
        benefit = make_benefit(
            "A_확정계산",
            실적조건=300_000,
        )
        result = calculate_card_benefit(
            make_card(
                benefit,
                previous_month_spending=500_000,
            ),
            payment_category="카페",
            payment_amount=10_000,
        )

        self.assertEqual(result["expected_benefit"], 1_000)
        self.assertTrue(result["performance_met"])
        self.assertEqual(result["required_spending"], 300_000)
        self.assertEqual(
            result["previous_month_spending"],
            500_000,
        )

    def test_performance_requirement_is_not_met(self):
        benefit = make_benefit(
            "A_확정계산",
            실적조건=300_000,
        )
        result = calculate_card_benefit(
            make_card(
                benefit,
                previous_month_spending=100_000,
            ),
            payment_category="카페",
            payment_amount=10_000,
        )

        self.assertEqual(result["expected_benefit"], 0)
        self.assertFalse(result["performance_met"])
        self.assertIn(
            "전월실적 미달",
            result["calculation_reason"],
        )

    def test_partially_used_monthly_limit(self):
        benefit = make_benefit(
            "A_확정계산",
            혜택값=20,
            월최대혜택액=5_000,
        )
        result = calculate_card_benefit(
            make_card(
                benefit,
                benefit_usage_this_month={"test-1": 4_000},
            ),
            payment_category="카페",
            payment_amount=10_000,
        )

        self.assertEqual(result["expected_benefit"], 1_000)
        self.assertEqual(result["monthly_limit"], 5_000)
        self.assertEqual(result["monthly_used"], 4_000)
        self.assertEqual(result["monthly_remaining"], 1_000)

    def test_fully_used_monthly_limit(self):
        benefit = make_benefit(
            "A_확정계산",
            혜택값=20,
            월최대혜택액=5_000,
        )
        result = calculate_card_benefit(
            make_card(
                benefit,
                benefit_usage_this_month={"test-1": 5_000},
            ),
            payment_category="카페",
            payment_amount=10_000,
        )

        self.assertEqual(result["expected_benefit"], 0)
        self.assertEqual(result["monthly_remaining"], 0)
        self.assertIn(
            "월 혜택 한도 소진",
            result["calculation_reason"],
        )

    def test_fully_used_card_total_limit(self):
        benefit = make_benefit("A_확정계산")
        result = calculate_card_benefit(
            make_card(
                benefit,
                monthly_total_limit=10_000,
                card_monthly_benefit_used=10_000,
            ),
            payment_category="카페",
            payment_amount=10_000,
        )

        self.assertEqual(result["expected_benefit"], 0)
        self.assertIn(
            "카드 통합한도 소진",
            result["calculation_reason"],
        )

    def test_user_selected_option_benefit(self):
        cafe_benefit = make_benefit(
            "A_확정계산",
            혜택ID="cafe-option",
            혜택값=10,
            옵션그룹="생활 옵션",
            옵션형=True,
            요약="카페 옵션",
        )
        convenience_benefit = make_benefit(
            "A_확정계산",
            혜택ID="store-option",
            혜택값=20,
            옵션그룹="생활 옵션",
            옵션형=True,
            요약="편의점 옵션",
        )
        card = make_card(
            cafe_benefit,
            benefits=[cafe_benefit, convenience_benefit],
            selected_option_benefit_id="cafe-option",
        )

        result = calculate_card_benefit(
            card,
            payment_category="카페",
            payment_amount=10_000,
        )

        self.assertEqual(result["expected_benefit"], 1_000)
        self.assertEqual(result["benefit_name"], "카페 옵션")
        self.assertTrue(result["option_selected"])
        self.assertEqual(
            result["option_selection_reason"],
            "사용자 선택 옵션",
        )

    def test_option_group_selects_maximum_expected_benefit(self):
        lower = make_benefit(
            "A_확정계산",
            혜택ID="option-1000",
            혜택값=10,
            옵션그룹="할인 옵션",
            옵션형=True,
            요약="천원 옵션",
        )
        higher = make_benefit(
            "A_확정계산",
            혜택ID="option-2000",
            혜택값=20,
            옵션그룹="할인 옵션",
            옵션형=True,
            요약="이천원 옵션",
        )

        result = calculate_card_benefit(
            make_card(lower, benefits=[lower, higher]),
            payment_category="카페",
            payment_amount=10_000,
        )

        self.assertEqual(result["expected_benefit"], 2_000)
        self.assertEqual(result["benefit_name"], "이천원 옵션")
        self.assertIn(
            "최대 기대혜택 옵션",
            result["option_selection_reason"],
        )

    def test_option_group_prefers_a_over_b_for_equal_amount(self):
        a_grade = make_benefit(
            "A_확정계산",
            혜택ID="a-option",
            옵션그룹="등급 옵션",
            옵션형=True,
            요약="A 옵션",
        )
        b_grade = make_benefit(
            "B_추정계산",
            혜택ID="b-option",
            옵션그룹="등급 옵션",
            옵션형=True,
            임시월캡=2_000,
            요약="B 옵션",
        )

        result = calculate_card_benefit(
            make_card(a_grade, benefits=[b_grade, a_grade]),
            payment_category="카페",
            payment_amount=10_000,
        )

        self.assertEqual(result["expected_benefit"], 1_000)
        self.assertEqual(result["scoring_grade"], "A_확정계산")
        self.assertEqual(result["benefit_name"], "A 옵션")

    def test_option_header_is_excluded(self):
        header = make_benefit(
            "A_확정계산",
            혜택ID="option-header",
            옵션그룹="헤더 옵션",
            옵션형=True,
            옵션헤더=True,
        )

        result = calculate_card_benefit(
            make_card(header),
            payment_category="카페",
            payment_amount=10_000,
        )

        self.assertEqual(result["expected_benefit"], 0)
        self.assertFalse(result["eligible"])
        self.assertIn(
            "옵션헤더",
            result["calculation_reason"],
        )

    def test_general_benefit_keeps_previous_behavior(self):
        result = calculate_card_benefit(
            make_card(make_benefit("A_확정계산")),
            payment_category="카페",
            payment_amount=10_000,
        )

        self.assertEqual(result["expected_benefit"], 1_000)
        self.assertIsNone(result["option_group"])
        self.assertFalse(result["is_option_benefit"])
        self.assertFalse(result["option_selected"])
        self.assertEqual(
            result["option_selection_reason"],
            "일반 혜택",
        )


if __name__ == "__main__":
    unittest.main()
