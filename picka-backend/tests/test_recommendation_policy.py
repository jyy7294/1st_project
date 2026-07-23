import unittest
from unittest.mock import patch

from app.services.recommendation_service import (
    calculate_performance_status,
    performance_priority_key,
    recommend_cards,
)


def card_result(
    card_id: int,
    benefit: int,
    *,
    remaining_before: int,
    reaches_target: bool,
    transaction_count: int = 0,
    current_month_spending: int = 0,
    is_conditional: bool = False,
) -> dict:
    return {
        "card_id": card_id,
        "card_name": f"카드 {card_id}",
        "expected_benefit": benefit,
        "eligible": benefit > 0,
        "is_conditional": is_conditional,
        "caveat": "적용 여부 확인 필요" if is_conditional else None,
        "reason": "혜택 계산 결과",
        "reason_details": [],
        "needs_performance": remaining_before > 0,
        "reaches_target_with_payment": reaches_target,
        "performance_required": 300_000,
        "performance_remaining_before": remaining_before,
        "performance_remaining_after": 0 if reaches_target else remaining_before,
        "performance_achievement_rate": 0.9,
        "monthly_transaction_count": transaction_count,
        "current_month_spending": current_month_spending,
    }


class RecommendationPolicyTest(unittest.TestCase):
    def test_performance_status_uses_current_month_spending(self):
        status = calculate_performance_status(
            {
                "required_spending": 300_000,
                "previous_month_spending": 216_000,
                "current_month_spending": 150_000,
            },
            payment_amount=22_000,
        )

        self.assertEqual(status["performance_current"], 150_000)
        self.assertEqual(status["performance_after_payment"], 172_000)
        self.assertEqual(status["performance_remaining_before"], 150_000)
        self.assertEqual(status["performance_remaining_after"], 128_000)

    def test_performance_ranking_ignores_previous_month_spending(self):
        cards = []
        for card_id, previous, current in (
            (1, 290_000, 100_000),
            (2, 10_000, 160_000),
        ):
            card = {
                "card_id": card_id,
                "required_spending": 300_000,
                "previous_month_spending": previous,
                "current_month_spending": current,
                "monthly_transaction_count": 0,
                "expected_benefit": 0,
            }
            cards.append({
                **card,
                **calculate_performance_status(card, payment_amount=22_000),
            })

        ranked = sorted(cards, key=performance_priority_key)
        self.assertEqual(ranked[0]["card_id"], 2)

    def recommend(self, results: list[dict]) -> dict:
        with patch(
            "app.services.recommendation_service.calculate_card_benefit",
            side_effect=results,
        ):
            return recommend_cards(
                merchant_name="테스트 가맹점",
                payment_category="테스트 업종",
                payment_amount=10_000,
                user_card_states=[{} for _ in results],
            )

    def test_larger_benefit_always_wins_even_by_one_won(self):
        result = self.recommend(
            [
                card_result(1, 1_001, remaining_before=100_000, reaches_target=False),
                card_result(2, 1_000, remaining_before=5_000, reaches_target=True),
            ]
        )

        self.assertEqual(result["recommended_card"]["card_id"], 1)
        self.assertEqual(result["recommendation_basis"], "benefit")

    def test_confirmed_benefit_ranks_before_larger_conditional_benefit(self):
        result = self.recommend(
            [
                card_result(1, 4_000, remaining_before=0, reaches_target=False),
                card_result(
                    2,
                    5_000,
                    remaining_before=0,
                    reaches_target=False,
                    is_conditional=True,
                ),
            ]
        )

        self.assertEqual(result["recommended_card"]["card_id"], 1)
        self.assertFalse(result["recommended_card"]["is_conditional"])

    def test_equal_benefits_use_performance_as_tiebreaker(self):
        result = self.recommend(
            [
                card_result(1, 1_000, remaining_before=100_000, reaches_target=False),
                card_result(2, 1_000, remaining_before=5_000, reaches_target=True),
            ]
        )

        self.assertEqual(result["recommended_card"]["card_id"], 2)
        self.assertEqual(result["recommendation_basis"], "performance_tiebreak")

    def test_no_benefits_use_performance(self):
        result = self.recommend(
            [
                card_result(1, 0, remaining_before=100_000, reaches_target=False),
                card_result(2, 0, remaining_before=5_000, reaches_target=True),
            ]
        )

        self.assertEqual(result["recommended_card"]["card_id"], 2)
        self.assertEqual(result["recommendation_basis"], "performance_only")

    def test_performance_prompt_offers_alternative_card(self):
        result = self.recommend(
            [
                card_result(1, 2_000, remaining_before=100_000, reaches_target=False),
                card_result(2, 1_000, remaining_before=5_000, reaches_target=True),
            ]
        )

        self.assertEqual(result["recommended_card"]["card_id"], 1)
        self.assertEqual(result["performance_prompt"]["card_id"], 2)
        self.assertEqual(result["performance_prompt"]["action_label"], "예")
        self.assertIn("이 카드로 결제하시겠습니까?", result["performance_prompt"]["message"])

    def test_equal_benefit_and_remaining_prefers_frequently_used_card(self):
        result = self.recommend(
            [
                card_result(
                    1,
                    1_000,
                    remaining_before=5_000,
                    reaches_target=True,
                    transaction_count=3,
                ),
                card_result(
                    2,
                    1_000,
                    remaining_before=5_000,
                    reaches_target=True,
                    transaction_count=8,
                ),
            ]
        )

        self.assertEqual(result["recommended_card"]["card_id"], 2)

    def test_no_benefit_and_no_performance_candidate_requires_user_selection(self):
        result = self.recommend(
            [
                card_result(1, 0, remaining_before=0, reaches_target=False),
                card_result(2, 0, remaining_before=0, reaches_target=False),
            ]
        )

        self.assertIsNone(result["recommended_card"])
        self.assertTrue(result["selection_required"])
        self.assertEqual(result["recommendation_basis"], "user_selection")
        self.assertEqual(len(result["selectable_cards"]), 2)
        self.assertEqual(
            result["saving_message"],
            "혜택이 적용되는 카드가 없습니다. 원하시는 카드로 결제하세요.",
        )


if __name__ == "__main__":
    unittest.main()
