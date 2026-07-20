from __future__ import annotations

from typing import Any

from app.services.recommendation_service import (
    calculate_base_benefit,
    calculate_card_benefit,
    calculate_scored_benefit,
    get_benefit_usage_this_month,
    get_card_monthly_benefit_used,
    get_field,
    get_option_metadata,
    get_previous_month_spending,
    get_scoring_grade,
    is_category_matched,
    is_option_header,
    select_option_candidates,
    should_exclude_from_calculation,
    to_non_negative_float,
)


def _merchant_condition(benefit: dict, merchant_name: str) -> tuple[Any, bool | None]:
    condition = get_field(
        benefit,
        "merchant_list",
        "가맹점목록",
        "merchant_condition",
    )
    if not condition:
        return condition, None

    values = condition if isinstance(condition, list) else str(condition).split("|")
    normalized_name = "".join(merchant_name.lower().split())
    matched = any(
        "".join(str(value).lower().split()) in normalized_name
        for value in values
        if value
    )
    return condition, matched


def _standard_reasons(
    benefit: dict,
    category_matched: bool,
    calculation: dict,
    base_benefit: float,
) -> list[str]:
    reasons: list[str] = []
    category = get_field(benefit, "category", "카테고리")
    grade = get_scoring_grade(benefit) or "A_확정계산"

    if category == "유의사항":
        reasons.append("유의사항")
    if is_option_header(benefit):
        reasons.append("옵션헤더")
    if grade == "C_표시전용":
        reasons.append("C_표시전용")
    if grade == "D_제외권장":
        reasons.append("D_제외권장")
    if not category_matched:
        reasons.append("카테고리 불일치")
    if calculation.get("performance_met") is False:
        reasons.append("전월실적 미달")
    if calculation.get("monthly_remaining") == 0:
        reasons.append("월 혜택 한도 소진")

    card_cap = calculation.get("_card_total_limit")
    card_used = calculation.get("_card_monthly_benefit_used", 0)
    if card_cap is not None and card_used >= card_cap:
        reasons.append("카드 통합한도 소진")
    if grade == "B_추정계산" and calculation.get("applied_cap") is None:
        reasons.append("B등급 한도 확인 필요")
    if base_benefit <= 0 and not should_exclude_from_calculation(benefit):
        reasons.append("할인율 또는 혜택 금액 없음")

    return list(dict.fromkeys(reasons))


def build_recommendation_debug(
    cards: list[dict],
    merchant_name: str,
    payment_category: str,
    payment_amount: int,
) -> dict:
    card_traces = []

    for card in cards:
        final_card = calculate_card_benefit(
            card=card,
            merchant_name=merchant_name,
            payment_category=payment_category,
            payment_amount=payment_amount,
        )
        benefit_traces = []
        option_candidates = []
        card_total_limit = to_non_negative_float(
            get_field(card, "monthly_total_limit", "통합한도_월")
        )
        card_used = get_card_monthly_benefit_used(card)

        for index, benefit in enumerate(card.get("benefits", [])):
            source_id = get_field(
                benefit,
                "source_benefit_id",
                "혜택ID",
                "benefit_id",
            )
            category_matched = is_category_matched(benefit, payment_category)
            used = get_benefit_usage_this_month(card, source_id)
            calculation = calculate_scored_benefit(
                card=card,
                benefit=benefit,
                payment_amount=payment_amount,
                benefit_used=used,
            )
            base_benefit = calculate_base_benefit(payment_amount, benefit)
            calculation["_card_total_limit"] = card_total_limit
            calculation["_card_monthly_benefit_used"] = card_used
            option = get_option_metadata(benefit)
            benefit_type = get_field(benefit, "benefit_type", "혜택유형")
            benefit_unit = get_field(benefit, "benefit_unit", "혜택단위")
            type_supported = benefit_type == "할인"
            unit_supported = benefit_unit in {"%", "원", "KRW"}
            pre_option_included = (
                not should_exclude_from_calculation(benefit)
                and type_supported
                and unit_supported
                and category_matched
                and calculation["expected_benefit"] > 0
            )
            merchant_condition, merchant_matched = _merchant_condition(
                benefit, merchant_name
            )
            reasons = _standard_reasons(
                benefit, category_matched, calculation, base_benefit
            )
            if not type_supported or not unit_supported:
                reasons.append("할인율 또는 혜택 금액 없음")

            trace = {
                "card_benefit_id": get_field(benefit, "card_benefit_id"),
                "source_benefit_id": source_id,
                "benefit_name": get_field(
                    benefit, "benefit_name", "혜택명", "source_summary"
                ),
                "category": get_field(benefit, "category", "카테고리"),
                "category_matched": category_matched,
                "merchant_condition": merchant_condition,
                "merchant_condition_matched": merchant_matched,
                "scoring_grade": get_scoring_grade(benefit) or "A_확정계산",
                "required_spending": calculation["required_spending"],
                "previous_month_spending": calculation[
                    "previous_month_spending"
                ],
                "performance_met": calculation["performance_met"],
                "base_benefit": int(base_benefit),
                "per_transaction_limit": to_non_negative_float(
                    get_field(
                        benefit, "per_transaction_limit", "한도_회당"
                    )
                ),
                "monthly_limit": calculation["monthly_limit"],
                "monthly_used": calculation["monthly_used"],
                "monthly_remaining": calculation["monthly_remaining"],
                "card_monthly_limit": card_total_limit,
                "card_monthly_benefit_used": int(card_used),
                "option_group": option["option_group"],
                "included": pre_option_included,
                "expected_benefit": (
                    calculation["expected_benefit"]
                    if pre_option_included
                    else 0
                ),
                "calculation_reason": calculation["calculation_reason"],
                "exclusion_reasons": list(dict.fromkeys(reasons)),
            }
            benefit_traces.append(trace)

            if pre_option_included:
                option_candidates.append(
                    {
                        "benefit_id": source_id,
                        "expected_benefit": calculation["expected_benefit"],
                        "scoring_grade": calculation["scoring_grade"],
                        "monthly_remaining": calculation["monthly_remaining"],
                        "option_group": option["option_group"],
                        "is_option_benefit": option["is_option_benefit"],
                        "_trace_index": index,
                    }
                )

        selected = select_option_candidates(card, option_candidates)
        selected_indexes = {item["_trace_index"] for item in selected}
        for index, trace in enumerate(benefit_traces):
            if trace["included"] and index not in selected_indexes:
                trace["included"] = False
                trace["expected_benefit"] = 0
                trace["exclusion_reasons"].append("옵션 미선택")
            if not trace["included"] and not trace["exclusion_reasons"]:
                trace["exclusion_reasons"].append("계산 가능한 혜택 없음")

        included_count = sum(trace["included"] for trace in benefit_traces)
        card_reasons = list(
            dict.fromkeys(
                reason
                for trace in benefit_traces
                if not trace["included"]
                for reason in trace["exclusion_reasons"]
            )
        )
        if final_card["expected_benefit"] == 0 and not card_reasons:
            card_reasons.append("계산 가능한 혜택 없음")

        card_traces.append(
            {
                "card_id": card["card_id"],
                "card_name": card["card_name"],
                "previous_month_spending": int(
                    get_previous_month_spending(card)
                ),
                "card_monthly_benefit_used": int(card_used),
                "candidate_benefit_count": len(benefit_traces),
                "matched_benefit_count": included_count,
                "expected_benefit": final_card["expected_benefit"],
                "reasons": card_reasons,
                "benefits": benefit_traces,
            }
        )

    return {
        "resolved_category": payment_category,
        "cards": card_traces,
    }
