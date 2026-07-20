from __future__ import annotations

import argparse
from collections import Counter
from typing import Any

from app.core.database import SessionLocal
from app.services.recommendation_debug_service import (
    build_recommendation_debug,
)
from app.services.recommendation_service import (
    get_field,
    get_scoring_grade,
    is_category_matched,
)
from app.services.user_state_adapter import (
    build_user_card_states,
    resolve_merchant_category,
)


def analyze(
    user_id: int,
    merchant_name: str,
    payment_amount: int,
    usage_month: str,
) -> dict[str, Any]:
    with SessionLocal() as db:
        states = build_user_card_states(db, user_id, usage_month)
        category = resolve_merchant_category(db, merchant_name)
        debug = build_recommendation_debug(
            states,
            merchant_name,
            category,
            payment_amount,
        )

    cards = []
    traces_by_card = {card["card_id"]: card for card in debug["cards"]}
    for state in states:
        benefits = state["benefits"]
        trace = traces_by_card[state["card_id"]]
        cards.append(
            {
                "card_id": state["card_id"],
                "card_name": state["card_name"],
                "total_benefits": len(benefits),
                "category_matches": sum(
                    is_category_matched(benefit, category)
                    for benefit in benefits
                ),
                "starbucks_merchant_matches": sum(
                    merchant_name.lower()
                    in str(
                        get_field(
                            benefit,
                            "merchant_list",
                            "가맹점목록",
                            default="",
                        )
                    ).lower()
                    for benefit in benefits
                ),
                "grade_counts": dict(
                    Counter(
                        get_scoring_grade(benefit) or "A_확정계산"
                        for benefit in benefits
                    )
                ),
                "required_spending_values": sorted(
                    {
                        get_field(
                            benefit,
                            "required_spending",
                            "실적조건",
                        )
                        for benefit in benefits
                    },
                    key=lambda value: (value is None, value or 0),
                ),
                "monthly_limit_values": sorted(
                    {
                        get_field(
                            benefit,
                            "monthly_benefit_limit",
                            "monthly_limit",
                        )
                        for benefit in benefits
                    },
                    key=lambda value: (value is None, value or 0),
                ),
                "expected_benefit": trace["expected_benefit"],
                "reason_counts": dict(
                    Counter(
                        reason
                        for benefit in trace["benefits"]
                        for reason in benefit["exclusion_reasons"]
                    )
                ),
                "matched_benefits": [
                    benefit
                    for benefit in trace["benefits"]
                    if benefit["category_matched"]
                    or benefit["merchant_condition_matched"]
                ],
            }
        )

    return {
        "user_id": user_id,
        "merchant_name": merchant_name,
        "payment_amount": payment_amount,
        "usage_month": usage_month,
        "resolved_category": category,
        "cards": cards,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", type=int, default=2)
    parser.add_argument("--merchant", default="스타벅스")
    parser.add_argument("--amount", type=int, default=12_000)
    parser.add_argument("--usage-month", default="2026-07")
    args = parser.parse_args()

    import json

    print(
        json.dumps(
            analyze(
                args.user_id,
                args.merchant,
                args.amount,
                args.usage_month,
            ),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
