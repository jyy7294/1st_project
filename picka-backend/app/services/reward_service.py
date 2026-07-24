from __future__ import annotations

import math
import re

from app.services.recommendation_service import (
    get_exclusion_reason,
    get_field,
    is_category_matched,
    is_spending_requirement_met,
    should_exclude_from_calculation,
)


PROGRAM_KEYWORDS = [
    ("스카이패스", "스카이패스"), ("대한항공", "스카이패스"),
    ("아시아나", "아시아나클럽"), ("마이신한포인트", "마이신한포인트"),
    ("M포인트", "M포인트"), ("포인트리", "포인트리"),
    ("NH포인트", "NH포인트"), ("네이버페이", "네이버페이 포인트"),
    ("쿠팡캐시", "쿠팡캐시"), ("모니머니", "모니머니"),
    ("빅포인트", "빅포인트"), ("메리어트 본보이", "메리어트 본보이 포인트"),
]


def infer_reward_program(text: str, issuer: str, reward_type: str) -> str:
    for keyword, program in PROGRAM_KEYWORDS:
        if keyword.lower() in text.lower():
            return program
    return f"{issuer} {'마일리지' if reward_type == 'mileage' else '포인트'}"


def calculate_transaction_rewards(
    card: dict,
    *,
    payment_category: str,
    payment_amount: int,
) -> list[dict]:
    rewards = []
    for benefit in card["benefits"]:
        benefit_type = get_field(benefit, "benefit_type", "혜택유형")
        if benefit_type not in {"포인트 적립", "마일리지 적립"}:
            continue
        if should_exclude_from_calculation(benefit) or get_exclusion_reason(benefit):
            continue
        if not is_category_matched(benefit, payment_category):
            continue
        if not is_spending_requirement_met(
            int(card.get("previous_month_spending", 0) or 0), benefit
        ):
            continue
        minimum = get_field(benefit, "minimum_payment", "건당최소금액", default=0) or 0
        if payment_amount < minimum:
            continue
        value = get_field(benefit, "benefit_value", "혜택값")
        unit = get_field(benefit, "benefit_unit", "혜택단위")
        if not isinstance(value, (int, float)) or value <= 0:
            continue
        text = " ".join(str(get_field(benefit, key, default="") or "") for key in (
            "benefit_name", "source_summary", "source_detail"
        ))
        if benefit_type == "포인트 적립" and unit == "%":
            amount = math.floor(payment_amount * float(value) / 100)
            reward_type, reward_unit = "point", "P"
        elif benefit_type == "마일리지 적립" and unit == "마일/천원":
            thousand_match = re.search(r"(\d+)\s*천\s*원\s*(?:당|마다)", text)
            won_match = re.search(r"([\d,]+)\s*원\s*(?:당|마다)", text)
            if thousand_match:
                denominator = int(thousand_match.group(1)) * 1000
            elif won_match:
                denominator = int(won_match.group(1).replace(",", ""))
            else:
                denominator = 1000
            amount = math.floor(payment_amount / denominator * float(value))
            reward_type, reward_unit = "mileage", "mile"
        else:
            continue
        limit = get_field(benefit, "monthly_benefit_limit", "월혜택한도")
        if isinstance(limit, (int, float)) and limit >= 0:
            amount = min(amount, math.floor(limit))
        if amount <= 0:
            continue
        rewards.append({
            "card_benefit_id": get_field(benefit, "card_benefit_id", "id"),
            "reward_type": reward_type,
            "reward_program": infer_reward_program(
                text, str(card.get("card_company") or "카드사"), reward_type
            ),
            "reward_amount": amount,
            "reward_unit": reward_unit,
        })
    return rewards
