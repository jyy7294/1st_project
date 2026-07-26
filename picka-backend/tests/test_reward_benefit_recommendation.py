from app.services.recommendation_service import calculate_card_benefit


def _card_with_point_benefit() -> dict:
    return {
        "card_id": 1,
        "card_name": "포인트 체크카드",
        "card_company": "테스트카드",
        "card_image": None,
        "previous_month_spending": 500_000,
        "required_spending": 0,
        "monthly_benefit_used": 0,
        "monthly_total_limit": None,
        "benefit_usage": {},
        "benefits": [{
            "source_benefit_id": "point-1",
            "category": "모든가맹점",
            "benefit_type": "포인트 적립",
            "benefit_value": 1,
            "benefit_unit": "%",
            "required_spending": None,
            "scoring_grade": "A_확정계산",
            "benefit_name": "모든 가맹점 1% 포인트 적립",
        }],
    }


def test_point_benefit_is_not_deducted_from_payment_by_default():
    result = calculate_card_benefit(
        _card_with_point_benefit(),
        payment_category="마트/쇼핑",
        payment_amount=10_000,
    )
    assert result["expected_benefit"] == 0


def test_point_benefit_is_monetized_for_new_card_recommendation():
    result = calculate_card_benefit(
        _card_with_point_benefit(),
        payment_category="마트/쇼핑",
        payment_amount=10_000,
        include_reward_benefits=True,
    )
    assert result["expected_benefit"] == 100

