from user_cards import get_user_cards

BENEFIT_SIMILAR_THRESHOLD = 500

def format_number(value: int | float) -> str:
    """정수로 표현 가능한 숫자에서는 불필요한 소수점을 제거합니다."""

    return f"{value:g}"


def build_success_reason(
    payment_category: str,
    benefit_rate: int | float,
    expected_benefit: int
) -> tuple[str, list[str]]:
    """적용된 혜택을 사용자 친화적인 요약과 상세 항목으로 만듭니다."""

    rate_text = format_number(benefit_rate)
    category_detail = f"{payment_category} 업종 할인 적용"

    reason = (
        f"{payment_category} 업종에서 {rate_text}% 할인 혜택이 적용되며, "
        "전월 실적 조건을 충족했습니다."
    )
    reason_details = [
        category_detail,
        "전월 실적 조건 충족",
        f"예상 혜택 {expected_benefit:,}원"
    ]

    return reason, reason_details


def get_benefit_categories(benefit: dict) -> list[str]:
    """
    혜택에서 적용 가능한 카테고리 목록을 추출합니다.

    예:
    카테고리: 배달앱
    카테고리목록: 배달앱|카페/디저트

    결과:
    ["배달앱", "카페/디저트"]
    """

    categories = []

    main_category = benefit.get("카테고리")

    if main_category:
        categories.append(main_category)

    category_list = benefit.get("카테고리목록")

    if category_list:
        categories.extend(category_list.split("|"))

    # 중복 제거
    return list(set(categories))


def is_category_matched(
    benefit: dict,
    payment_category: str
) -> bool:
    """
    결제 업종이 카드 혜택 대상인지 확인합니다.
    """

    benefit_categories = get_benefit_categories(benefit)

    # 모든 가맹점 혜택
    if "모든가맹점" in benefit_categories:
        return True

    # 결제 카테고리와 혜택 카테고리가 일치
    return payment_category in benefit_categories


def is_spending_requirement_met(
    previous_month_spending: int,
    benefit: dict
) -> bool:
    """
    사용자의 전월 실적이 혜택 조건을 충족했는지 확인합니다.
    """

    required_spending = benefit.get("실적조건")

    # 실적조건이 없으면 조건 없이 적용
    if required_spending is None:
        return True

    return previous_month_spending >= required_spending


def calculate_percent_discount(
    payment_amount: int,
    benefit: dict,
    monthly_benefit_used: int
) -> int:
    """
    퍼센트 할인 혜택의 예상 할인금액을 계산합니다.
    """

    benefit_value = benefit.get("혜택값")

    if benefit_value is None:
        return 0

    # 예: 12,000원 × 10%
    expected_discount = payment_amount * benefit_value / 100

    # 건당 할인한도 적용
    per_transaction_limit = benefit.get("한도_회당")

    if per_transaction_limit is not None:
        expected_discount = min(
            expected_discount,
            per_transaction_limit
        )

    # 월 최대 혜택액 적용
    monthly_limit = benefit.get("월최대혜택액")

    if monthly_limit is not None:
        remaining_limit = max(
            monthly_limit - monthly_benefit_used,
            0
        )

        expected_discount = min(
            expected_discount,
            remaining_limit
        )

    return int(expected_discount)
def build_recommendation_reason(
    payment_category: str,
    benefit_rate: float,
    expected_benefit: int,
    required_spending: float | None,
    previous_month_spending: int
) -> tuple[str, list[str]]:
    """
    프론트 화면에 표시할 추천 이유 문장과 상세 항목을 생성합니다.
    """

    reason_details = []

    # 1. 업종 혜택
    reason_details.append(
        f"{payment_category} 업종에서 {benefit_rate:g}% 할인 적용"
    )

    # 2. 전월 실적
    if required_spending is None:
        reason_details.append(
            "전월 실적 조건 없이 혜택 적용"
        )
    else:
        reason_details.append(
            f"전월 실적 {int(required_spending):,}원 조건 충족"
        )

    # 3. 예상 혜택
    reason_details.append(
        f"예상 혜택 {expected_benefit:,}원"
    )

    if required_spending is None:
        reason = (
            f"{payment_category} 업종에서 "
            f"{benefit_rate:g}% 할인 혜택이 적용됩니다. "
            f"예상 혜택은 {expected_benefit:,}원입니다."
        )
    else:
        reason = (
            f"{payment_category} 업종에서 "
            f"{benefit_rate:g}% 할인 혜택이 적용되며, "
            f"전월 실적 조건을 충족했습니다. "
            f"예상 혜택은 {expected_benefit:,}원입니다."
        )

    return reason, reason_details

def calculate_performance_status(
    card: dict,
    payment_amount: int
) -> dict:
    """
    이번 결제를 해당 카드로 했을 때
    전월 실적 달성 상태를 계산합니다.
    """

    required = int(
        card.get("required_spending", 0) or 0
    )

    current = int(
        card.get("previous_month_spending", 0) or 0
    )

    after_payment = current + payment_amount

    remaining_before = max(
        required - current,
        0
    )

    remaining_after = max(
        required - after_payment,
        0
    )

    # 원래 실적을 아직 달성하지 않은 카드인지
    needs_performance = (
        required > 0
        and current < required
    )

    # 이번 결제로 실적 기준을 달성하는지
    reaches_target = (
        needs_performance
        and after_payment >= required
    )

    if required <= 0:
        achievement_rate = 1.0
    else:
        achievement_rate = min(
            current / required,
            1.0
        )

    return {
        "performance_required": required,
        "performance_current": current,
        "performance_after_payment": after_payment,
        "performance_remaining_before": remaining_before,
        "performance_remaining_after": remaining_after,
        "performance_achievement_rate": round(
            achievement_rate,
            4
        ),
        "needs_performance": needs_performance,
        "reaches_target_with_payment": reaches_target
    }
def select_card_by_performance(
    candidates: list[dict]
) -> dict | None:

    if not candidates:
        return None

    return min(
        candidates,
        key=performance_priority_key
    )

def calculate_card_benefit(
    card: dict,
    payment_category: str,
    payment_amount: int
) -> dict:

    applicable_benefits = []
    failure_reasons = []

    performance_status = calculate_performance_status(
    card=card,
    payment_amount=payment_amount
)

    for benefit in card["benefits"]:

        if benefit.get("혜택유형") != "할인":
            continue

        if benefit.get("혜택단위") != "%":
            continue

        if not is_category_matched(
            benefit,
            payment_category
        ):
            continue

        required_spending = benefit.get("실적조건")

        if (
            required_spending is not None
            and card["previous_month_spending"]
            < required_spending
        ):
            failure_reasons.append(
                f"전월 실적 {int(required_spending):,}원 조건 미충족"
            )
            continue


        expected_benefit = calculate_percent_discount(
            payment_amount=payment_amount,
            benefit=benefit,
            monthly_benefit_used=card[
                "monthly_benefit_used"
            ]
        )

        if expected_benefit <= 0:
            failure_reasons.append(
                "월 혜택 한도가 소진되었습니다."
            )
            continue

        applicable_benefits.append({
            "benefit_id": benefit.get("혜택ID"),
            "expected_benefit": expected_benefit,
            "benefit_rate": benefit.get("혜택값"),
            "summary": benefit.get("요약"),
            "required_spending": required_spending
        })

    if not applicable_benefits:
        reason = (
            failure_reasons[0]
            if failure_reasons
            else "현재 결제 업종에 적용 가능한 혜택이 없습니다."
        )

        return {
            "card_id": card["card_id"],
            "card_name": card["card_name"],
            "card_company": card["card_company"],
            "card_image": card["card_image"],
            "expected_benefit": 0,
            "eligible": False,
            "reason": reason,
            "reason_details": [reason, "예상 혜택 0원"],
            **performance_status
        }

    best_benefit = max(
        applicable_benefits,
        key=lambda item: item["expected_benefit"]
    )

    reason, reason_details = build_recommendation_reason(
        payment_category=payment_category,
        benefit_rate=best_benefit["benefit_rate"],
        expected_benefit=best_benefit["expected_benefit"],
        required_spending=best_benefit["required_spending"],
        previous_month_spending=card[
            "previous_month_spending"
        ]
    )
    reason, reason_details = build_success_reason(
        payment_category=payment_category,
        benefit_rate=best_benefit["benefit_rate"],
        expected_benefit=best_benefit["expected_benefit"]
    )

    return {
        "card_id": card["card_id"],
        "card_name": card["card_name"],
        "card_company": card["card_company"],
        "card_image": card["card_image"],
        "expected_benefit": best_benefit[
            "expected_benefit"
        ],
        "eligible": True,
        "benefit_rate": best_benefit["benefit_rate"],
        "reason": reason,
        "reason_details": reason_details,
        "benefit_summary": best_benefit["summary"],
        "required_spending": best_benefit[
            "required_spending"
        ],
        "previous_month_spending": card[
            "previous_month_spending"
        ],
        **performance_status
    }
def performance_priority_key(
    card: dict
) -> tuple:
    """
    실적 달성에 유리한 카드가 먼저 오도록
    정렬 기준을 반환합니다.
    """

    required = card.get(
        "performance_required",
        0
    )

    needs_performance = card.get(
        "needs_performance",
        False
    )

    reaches_target = card.get(
        "reaches_target_with_payment",
        False
    )

    remaining_after = card.get(
        "performance_remaining_after",
        float("inf")
    )

    achievement_rate = card.get(
        "performance_achievement_rate",
        0
    )

    # 우선순위
    # 1. 실적 조건이 있고 아직 달성하지 않은 카드
    # 2. 이번 결제로 실적을 바로 달성하는 카드
    # 3. 결제 후 남는 실적금액이 적은 카드
    # 4. 현재 달성률이 높은 카드
    # 5. 예상 혜택이 큰 카드
    return (
        not (
            required > 0
            and needs_performance
        ),
        not reaches_target,
        remaining_after,
        -achievement_rate,
        -card.get("expected_benefit", 0)
    )
def rank_cards(
    results: list[dict]
) -> tuple[list[dict], str]:
    """
    혜택과 실적을 함께 고려해
    전체 카드 순위를 생성합니다.
    """

    if not results:
        return [], "none"

    # 우선 예상 혜택 기준으로 정렬
    benefit_sorted = sorted(
        results,
        key=lambda card: card[
            "expected_benefit"
        ],
        reverse=True
    )

    best_benefit = benefit_sorted[0][
        "expected_benefit"
    ]

    # 모든 카드의 예상 혜택이 0원인 경우
    if best_benefit <= 0:
        ranked = sorted(
            benefit_sorted,
            key=performance_priority_key
        )

        return ranked, "performance_only"

    # 최고 혜택 카드와 500원 이내 차이인 카드들
    similar_cards = [
        card
        for card in benefit_sorted
        if (
            best_benefit
            - card["expected_benefit"]
            <= BENEFIT_SIMILAR_THRESHOLD
        )
    ]

    # 혜택 차이가 비슷한 카드가 2장 이상인 경우
    if len(similar_cards) >= 2:
        similar_ranked = sorted(
            similar_cards,
            key=performance_priority_key
        )

        similar_card_ids = {
            card["card_id"]
            for card in similar_cards
        }

        # 비슷한 혜택 그룹 밖에 있는 카드
        remaining_cards = [
            card
            for card in benefit_sorted
            if card["card_id"]
            not in similar_card_ids
        ]

        # 나머지는 혜택순으로 유지
        ranked = (
            similar_ranked
            + remaining_cards
        )

        return ranked, "performance_tiebreak"

    # 혜택 차이가 충분히 큰 경우
    return benefit_sorted, "benefit"

def recommend_cards(
    merchant_name: str,
    payment_category: str,
    payment_amount: int
) -> dict:
    """
    사용자의 모든 보유카드를 비교하고 추천 순위를 반환합니다.

    추천 기준:
    1. 혜택 차이가 크면 예상 혜택이 큰 카드 추천
    2. 혜택 차이가 500원 이하이면 실적 달성에 유리한 카드 추천
    3. 모든 카드 혜택이 0원이면 실적 달성에 유리한 카드 추천
    """

    user_cards = get_user_cards()
    results = []

    # 1. 보유카드별 예상 혜택 계산
    for card in user_cards:
        card_result = calculate_card_benefit(
            card=card,
            payment_category=payment_category,
            payment_amount=payment_amount
        )

        results.append(card_result)

    # 카드가 하나도 없는 경우
    if not results:
        return {
            "transaction": {
                "merchant_name": merchant_name,
                "category": payment_category,
                "amount": payment_amount
            },
            "recommendation_basis": "none",
            "recommended_card": None,
            "additional_saving": 0,
            "saving_message": "추천 가능한 카드가 없습니다.",
            "other_cards": [],
            "comparison": []
        }

    # 2. 우선 예상 혜택이 큰 순서로 정렬
    results.sort(
        key=lambda item: item["expected_benefit"],
        reverse=True
    )

    best_benefit_amount = results[0][
        "expected_benefit"
    ]

    second_benefit_amount = (
        results[1]["expected_benefit"]
        if len(results) >= 2
        else 0
    )

    benefit_gap = (
        best_benefit_amount
        - second_benefit_amount
    )

    # 3. 최종 추천 카드 결정
    if best_benefit_amount <= 0:
        # 모든 카드 혜택이 0원
        recommended_card = select_card_by_performance(
            results
        )

        recommendation_basis = "performance_only"

    elif (
        len(results) >= 2
        and benefit_gap
        <= BENEFIT_SIMILAR_THRESHOLD
    ):
        # 최고 혜택과 500원 이내인 카드만 후보로 선정
        similar_cards = [
            card
            for card in results
            if (
                best_benefit_amount
                - card["expected_benefit"]
                <= BENEFIT_SIMILAR_THRESHOLD
            )
        ]

        recommended_card = select_card_by_performance(
            similar_cards
        )

        recommendation_basis = "performance_tiebreak"

    else:
        # 혜택 차이가 크면 혜택 1위 카드 추천
        recommended_card = results[0]

        recommendation_basis = "benefit"

    # 혹시 실적 추천 함수에서 None이 반환되면
    # 기존 혜택 1위 카드 사용
    if recommended_card is None:
        recommended_card = results[0]
        recommendation_basis = "benefit"

    # 4. 최종 추천카드를 목록 맨 앞으로 이동
    recommended_card_id = recommended_card["card_id"]

    results = [
        recommended_card
    ] + [
        card
        for card in results
        if card["card_id"] != recommended_card_id
    ]

    # 5. 최종 순위와 추천 여부 부여
    for index, result in enumerate(
        results,
        start=1
    ):
        result["rank"] = index
        result["is_recommended"] = (
            index == 1
        )

    recommended_card = (
        results[0]
        if results
        else None
    )

    # 6. 혜택 기준 1위 금액과 차이 계산
    # 최종 순위가 실적 기준으로 바뀔 수 있으므로,
    # 혜택 최고 금액은 기존 값으로 비교
    for result in results:
        result["difference_from_best_benefit"] = max(
            best_benefit_amount
            - result["expected_benefit"],
            0
        )

    # 7. 추천 이유 수정
    if recommended_card is not None:

        if recommendation_basis == "performance_only":
            remaining = recommended_card.get(
                "performance_remaining_after",
                0
            )

            if recommended_card.get(
                "reaches_target_with_payment",
                False
            ):
                recommended_card["reason"] = (
                    "현재 결제에서 적용 가능한 혜택이 없어, "
                    "이번 결제로 실적 기준을 달성할 수 있는 "
                    "카드를 추천합니다."
                )
            else:
                recommended_card["reason"] = (
                    "현재 결제에서 적용 가능한 혜택이 없어, "
                    "전월 실적 달성에 가장 유리한 "
                    "카드를 추천합니다."
                )

            recommended_card["reason_details"] = [
                "현재 거래의 즉시 혜택 없음",
                (
                    f"결제 후 남은 실적 "
                    f"{remaining:,}원"
                )
            ]

        elif recommendation_basis == "performance_tiebreak":
            remaining = recommended_card.get(
                "performance_remaining_after",
                0
            )

            original_reason = recommended_card.get(
                "reason",
                ""
            )

            recommended_card["reason"] = (
                "카드별 예상 혜택 차이가 크지 않아, "
                "전월 실적 달성에 더 유리한 "
                "카드를 추천합니다."
            )

            recommended_card["reason_details"] = [
                "유사한 예상 혜택의 카드 중 선정",
                (
                    f"결제 후 남은 실적 "
                    f"{remaining:,}원"
                ),
                original_reason
            ]

        else:
            recommended_card["reason_details"].append(
                "보유카드 중 예상 혜택이 가장 큼"
            )

    # 8. 사용자가 추천 카드를 거절했을 때 보여줄 목록
    other_cards = (
        results[1:]
        if len(results) > 1
        else []
    )

    # 9. 카드별 순위 표시 이유
    for card in results:
        if card["rank"] == 1:
            card["ranking_reason"] = (
                "픽카 최종 추천"
            )

        elif card["expected_benefit"] > 0:
            card["ranking_reason"] = (
                f"예상 혜택 "
                f"{card['expected_benefit']:,}원"
            )

        elif card.get(
            "needs_performance",
            False
        ):
            remaining = card.get(
                "performance_remaining_after",
                0
            )

            card["ranking_reason"] = (
                f"결제 후 실적까지 "
                f"{remaining:,}원 남음"
            )

        else:
            card["ranking_reason"] = (
                "현재 거래에서 적용 가능한 혜택 없음"
            )

    # 10. 절약 차이 계산
    recommended_benefit = recommended_card.get(
        "expected_benefit",
        0
    )

    next_card_benefit = (
        other_cards[0]["expected_benefit"]
        if other_cards
        else 0
    )

    additional_saving = max(
        recommended_benefit
        - next_card_benefit,
        0
    )

    # 실적 기준 추천에서는
    # 더 절약한다는 문장을 사용하면 안 됨
    if recommendation_basis == "benefit":
        if additional_saving > 0:
            saving_message = (
                f"다음 순위 카드보다 "
                f"{additional_saving:,}원을 "
                f"더 절약할 수 있습니다."
            )
        else:
            saving_message = (
                "다음 순위 카드와 예상 혜택이 동일합니다."
            )

    elif recommendation_basis == "performance_tiebreak":
        saving_message = (
            "예상 혜택 차이가 크지 않아 "
            "전월 실적 달성에 유리한 카드를 추천했습니다."
        )

    else:
        saving_message = (
            "적용 가능한 즉시 혜택이 없어 "
            "전월 실적 달성에 유리한 카드를 추천했습니다."
        )

    return {
        "transaction": {
            "merchant_name": merchant_name,
            "category": payment_category,
            "amount": payment_amount
        },
        "recommendation_basis": recommendation_basis,
        "recommended_card": recommended_card,
        "additional_saving": additional_saving,
        "saving_message": saving_message,
        "other_cards": other_cards,
        "comparison": results
    }


if __name__ == "__main__":
    recommendation = recommend_cards(
    merchant_name="성신문구",
    payment_category="문구",
    payment_amount=20000
)

    print("=" * 60)
    print("픽카 카드 추천 결과")
    print("=" * 60)

    print(
        f"가맹점: "
        f"{recommendation['transaction']['merchant_name']}"
    )
    print(
        f"업종: "
        f"{recommendation['transaction']['category']}"
    )
    print(
        f"결제금액: "
        f"{recommendation['transaction']['amount']:,}원"
    )

    print("\n[추천 순위]")

    for card in recommendation["comparison"]:
        print("-" * 60)
        print(f"{card['rank']}위")
        print(f"카드명: {card['card_name']}")
        print(
            f"예상 혜택: "
            f"{card['expected_benefit']:,}원"
        )
        print(f"추천 이유: {card['reason']}")

    recommended_card = recommendation[
        "recommended_card"
    ]

    print("\n[최종 추천 카드]")

    if recommended_card:
        print(recommended_card["card_name"])
        print(
            f"예상 혜택: "
            f"{recommended_card['expected_benefit']:,}원"
        )
