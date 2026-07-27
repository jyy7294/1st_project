from app.models import CardBenefit
from app.services.user_state_adapter import (
    _display_fields,
    _is_notice_benefit,
)


def test_fixed_annual_mileage_bonus_gets_truthful_display_metadata():
    benefit = CardBenefit(
        category="멤버십/포인트",
        benefit_type="마일리지 적립",
        benefit_value=0.0,
        benefit_unit="마일/천원",
        source_summary=(
            "트래블마일 15,000마일 보너스 적립 "
            "(연 1회, 1년차 300만원 / 2년차 이후 1,200만원 이상 사용 시)"
        ),
    )

    result = _display_fields(benefit)

    assert result["display_benefit_value"] == 15_000
    assert result["display_benefit_unit"] == "마일"
    assert result["display_value_text"] == "조건 충족 시 15,000마일"
    assert result["display_limit_text"] == "연 1회"
    assert result["is_transaction_calculable"] is False
    assert result["display_review_required"] is False


def test_zero_rate_is_not_exposed_as_a_real_display_rate():
    benefit = CardBenefit(
        benefit_type="마일리지 적립",
        benefit_value=0.0,
        benefit_unit="마일/천원",
        source_summary="구조화되지 않은 적립 안내",
    )

    result = _display_fields(benefit)

    assert result["display_benefit_value"] is None
    assert result["display_benefit_unit"] is None
    assert result["display_review_required"] is True


def test_notice_row_is_not_a_benefit():
    assert _is_notice_benefit(CardBenefit(category="유의사항")) is True
    assert _is_notice_benefit(CardBenefit(category="카페/디저트")) is False
