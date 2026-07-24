import logging

from app.services.category_normalization import normalize_payment_category
from app.services.llm_service import (
    LLMServiceError,
    judge_ambiguous_benefit,
)

logger = logging.getLogger(__name__)

DEFAULT_BENEFIT_DETAIL = (
    "상세 유의사항은 카드사 공식 상품설명서를 확인해 주세요."
)
EXCLUDED_SCORING_GRADES = {
    "C_표시전용",
    "D_제외권장",
}


def get_field(
    source: dict | object,
    *names: str,
    default=None,
):
    """한글 JSON 키와 영문 ORM 속성을 같은 방식으로 읽습니다."""

    for name in names:
        if isinstance(source, dict):
            value = source.get(name)
        else:
            value = getattr(source, name, None)

        if value is not None:
            return value

    return default


def to_non_negative_float(value) -> float | None:
    """한도와 사용액을 계산 가능한 0 이상의 숫자로 변환합니다."""

    if value is None:
        return None

    try:
        return max(float(value), 0)
    except (TypeError, ValueError):
        return None


def format_number(value: int | float) -> str:
    """정수로 표현 가능한 숫자에서는 불필요한 소수점을 제거합니다."""

    return f"{value:g}"


def build_success_reason(
    payment_category: str,
    benefit_rate: int | float,
    expected_benefit: int,
    benefit_unit: str | None = "%",
) -> tuple[str, list[str]]:
    """적용된 혜택을 사용자 친화적인 요약과 상세 항목으로 만듭니다."""

    benefit_text = (
        f"{format_number(benefit_rate)}% 할인"
        if benefit_unit == "%"
        else f"{expected_benefit:,}원 할인"
    )
    category_detail = f"{payment_category} 업종 할인 적용"

    reason = (
        f"{payment_category} 업종에서 {benefit_text} 혜택이 적용되며, "
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

    main_category = get_field(
        benefit,
        "카테고리",
        "category",
    )

    if main_category:
        categories.append(main_category)

    category_list = get_field(
        benefit,
        "카테고리목록",
        "category_list",
    )

    if category_list:
        categories.extend(category_list.split("|"))

    # 중복 제거
    return list(set(categories))


def get_scoring_grade(benefit: dict) -> str | None:
    """JSON 또는 DB 변환 결과에서 스코어링 등급을 가져옵니다."""

    scoring_grade = get_field(
        benefit,
        "스코어링등급",
        "scoring_grade",
    )

    if scoring_grade:
        return scoring_grade

    additional_conditions = get_field(
        benefit,
        "additional_conditions",
    )

    if isinstance(additional_conditions, dict):
        return additional_conditions.get("scoring_grade")

    return None

LLM_REVIEW_KEYWORDS = [
    "일부 입점 매장",
    "일부 매장",
    "입점 매장 제외",
    "제휴 가맹점",
    "지정 가맹점",
    "카드사 등록 가맹점",
    "특정 가맹점",
]

ITEM_CAVEAT_KEYWORDS = [
    "상품권",
    "선불카드",
    "기프트카드",
    "충전",
]

ITEM_CAVEAT_MESSAGE = "상품권·선불카드·충전 등 일부 품목은 혜택에서 제외될 수 있습니다."


def get_benefit_rule_text(
    benefit: dict | object,
) -> str:
    """
    DB에서 가져온 혜택의 요약·상세 문구를 하나로 합칩니다.
    """

    summary = get_field(
        benefit,
        "source_summary",
        "요약",
        "benefit_name",
        "혜택명",
        default="",
    )

    detail = get_field(
        benefit,
        "source_detail",
        "상세",
        default="",
    )

    additional_conditions = get_field(
        benefit,
        "additional_conditions",
        default={},
    )

    additional_text = ""

    if isinstance(additional_conditions, dict):
        additional_text = " ".join(
            str(value)
            for value in additional_conditions.values()
            if value is not None
        )

    return " ".join(
        str(value).strip()
        for value in (
            summary,
            detail,
            additional_text,
        )
        if value
    )


def should_use_llm(
    benefit: dict | object,
) -> bool:
    if get_exclusion_reason(benefit) is not None:
        return False

    rule_text = get_benefit_rule_text(benefit)

    if not rule_text:
        return False

    return any(
        keyword in rule_text
        for keyword in LLM_REVIEW_KEYWORDS
    )


def get_item_caveat(benefit: dict | object) -> str | None:
    rule_text = get_benefit_rule_text(benefit)
    if any(keyword in rule_text for keyword in ITEM_CAVEAT_KEYWORDS):
        return ITEM_CAVEAT_MESSAGE
    return None


def get_option_field(
    benefit: dict | object,
    *names: str,
    default=None,
):
    value = get_field(benefit, *names)

    if value is not None:
        return value

    additional_conditions = get_field(
        benefit,
        "additional_conditions",
    )

    if isinstance(additional_conditions, dict):
        return get_field(
            additional_conditions,
            *names,
            default=default,
        )

    return default


def is_truthy(value) -> bool:
    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return value == 1

    if isinstance(value, str):
        return value.strip().lower() in {
            "true",
            "1",
            "yes",
            "y",
            "예",
        }

    return False


def is_option_header(benefit: dict | object) -> bool:
    return is_truthy(
        get_option_field(
            benefit,
            "옵션헤더",
            "is_option_header",
            default=False,
        )
    )


def get_option_metadata(benefit: dict | object) -> dict:
    option_group = get_option_field(
        benefit,
        "옵션그룹",
        "option_group",
    )
    option_flag = is_truthy(
        get_option_field(
            benefit,
            "옵션형",
            "is_option",
            "option_enabled",
            default=False,
        )
    )

    return {
        "option_group": option_group,
        "is_option_benefit": bool(option_group) or option_flag,
    }


def get_exclusion_reason(benefit: dict | object) -> str | None:
    category = get_field(
        benefit,
        "카테고리",
        "category",
    )

    if category == "유의사항":
        return "유의사항 행은 추천 금액 계산에서 제외"

    if is_option_header(benefit):
        return "옵션헤더 행은 추천 금액 계산에서 제외"

    scoring_grade = get_scoring_grade(benefit)

    if scoring_grade in EXCLUDED_SCORING_GRADES:
        return f"{scoring_grade} 등급은 추천 금액 계산에서 제외"

    return None


def should_exclude_from_calculation(benefit: dict) -> bool:
    """표시 전용이거나 제외 권장인 혜택은 금액 계산에서 제외합니다."""

    return get_exclusion_reason(benefit) is not None


def get_benefit_display_fields(benefit: dict) -> dict:
    """추천 API에 사용할 혜택 요약과 상세 문구를 만듭니다."""

    summary = (
        get_field(
            benefit,
            "source_summary",
            "요약",
            "benefit_name",
            "혜택명",
        )
    )
    detail = (
        get_field(
            benefit,
            "source_detail",
            "상세",
            default=DEFAULT_BENEFIT_DETAIL,
        )
    )

    return {
        "benefit_name": get_field(
            benefit,
            "benefit_name",
            "혜택명",
            default=summary,
        ),
        "summary": summary,
        "detail": detail,
    }


def option_candidate_sort_key(candidate: dict) -> tuple:
    grade_priority = {
        "A_확정계산": 0,
        "B_추정계산": 1,
    }.get(candidate.get("scoring_grade"), 2)
    monthly_remaining = candidate.get("monthly_remaining")

    return (
        -candidate.get("expected_benefit", 0),
        grade_priority,
        -(
            monthly_remaining
            if monthly_remaining is not None
            else -1
        ),
        str(candidate.get("benefit_id") or ""),
    )


def select_option_candidates(
    card: dict | object,
    candidates: list[dict],
) -> list[dict]:
    """옵션그룹마다 현재 결제에 사용할 후보를 최대 1개로 줄입니다."""

    general_candidates = [
        candidate
        for candidate in candidates
        if not candidate["is_option_benefit"]
    ]
    option_candidates = [
        candidate
        for candidate in candidates
        if candidate["is_option_benefit"]
    ]

    for candidate in general_candidates:
        candidate["option_selected"] = False
        candidate["option_selection_reason"] = "일반 혜택"

    selected_benefit_id = get_field(
        card,
        "selected_option_benefit_id",
    )
    selected_option_group = get_field(
        card,
        "selected_option_group",
    )

    if selected_benefit_id is not None:
        selected = [
            candidate
            for candidate in option_candidates
            if str(candidate.get("benefit_id"))
            == str(selected_benefit_id)
        ]

        for candidate in selected:
            candidate["option_selected"] = True
            candidate["option_selection_reason"] = "사용자 선택 옵션"

        return general_candidates + selected

    if selected_option_group is not None:
        selected_group_candidates = [
            candidate
            for candidate in option_candidates
            if candidate.get("option_group")
            == selected_option_group
        ]

        if selected_group_candidates:
            selected = min(
                selected_group_candidates,
                key=option_candidate_sort_key,
            )
            selected["option_selected"] = True
            selected["option_selection_reason"] = "사용자 선택 옵션"
            return general_candidates + [selected]

        return general_candidates

    candidates_by_group: dict[str, list[dict]] = {}

    for candidate in option_candidates:
        option_group = candidate.get("option_group")

        if option_group is None:
            # 옵션형 표시만 있고 그룹이 없는 경우 독립 옵션으로 취급합니다.
            option_group = f"__benefit__:{candidate.get('benefit_id')}"

        candidates_by_group.setdefault(
            str(option_group),
            [],
        ).append(candidate)

    selected_options = []

    for group_candidates in candidates_by_group.values():
        selected = min(
            group_candidates,
            key=option_candidate_sort_key,
        )
        selected["option_selected"] = True
        selected["option_selection_reason"] = "최대 기대혜택 옵션"
        selected_options.append(selected)

    return general_candidates + selected_options


def is_category_matched(
    benefit: dict,
    payment_category: str
) -> bool:

    # 모든 가맹점이면 무조건 적용
    category = get_field(
        benefit,
        "카테고리",
        "category",
    )

    if category == "모든가맹점":
        return True

    # 기본 카테고리
    if normalize_payment_category(category) == normalize_payment_category(
        payment_category
    ):
        return True

    # 카테고리목록 확인
    category_list = get_field(
        benefit,
        "카테고리목록",
        "category_list",
    )

    if category_list:

        categories = [
            item.strip()
            for item in category_list.split("|")
        ]

        if normalize_payment_category(payment_category) in {
            normalize_payment_category(item) for item in categories
        }:
            return True

    return False


def is_spending_requirement_met(
    previous_month_spending: int,
    benefit: dict
) -> bool:
    """
    사용자의 전월 실적이 혜택 조건을 충족했는지 확인합니다.
    """

    required_spending = get_field(
        benefit,
        "실적조건",
        "required_spending",
    )

    # 실적조건이 없으면 조건 없이 적용
    if required_spending is None:
        return True

    return previous_month_spending >= required_spending


def calculate_percent_discount(
    payment_amount: int,
    benefit: dict,
    benefit_used: int
) -> int:
    """
    퍼센트 할인 혜택의 예상 할인금액을 계산합니다.

    적용 순서:
    1. 결제금액 × 할인율
    2. 건당 할인한도
    3. 해당 혜택의 월 잔여한도
    """

    benefit_value = benefit.get("혜택값")

    if benefit_value is None:
        return 0

    # 예: 12,000원 × 10%
    expected_discount = (
        payment_amount
        * benefit_value
        / 100
    )

    # 1. 건당 할인한도 적용
    per_transaction_limit = benefit.get(
        "한도_회당"
    )

    if per_transaction_limit is not None:
        expected_discount = min(
            expected_discount,
            per_transaction_limit
        )

    # 2. 혜택별 월 최대 혜택액 적용
    monthly_limit = benefit.get(
        "월최대혜택액"
    )

    if monthly_limit is not None:
        remaining_limit = max(
            monthly_limit - benefit_used,
            0
        )

        expected_discount = min(
            expected_discount,
            remaining_limit
        )

    return int(expected_discount)

    return int(expected_discount)
def build_recommendation_reason(
    payment_category: str,
    benefit_rate: float,
    expected_benefit: int,
    required_spending: float | None,
    previous_month_spending: int,
    benefit_unit: str | None = "%",
) -> tuple[str, list[str]]:
    """
    프론트 화면에 표시할 추천 이유 문장과 상세 항목을 생성합니다.
    """

    reason_details = []

    # 1. 업종 혜택
    benefit_text = (
        f"{benefit_rate:g}% 할인"
        if benefit_unit == "%"
        else f"{expected_benefit:,}원 할인"
    )
    reason_details.append(f"{payment_category} 업종에서 {benefit_text} 적용")

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
            f"{benefit_text} 혜택이 적용됩니다. "
            f"예상 혜택은 {expected_benefit:,}원입니다."
        )
    else:
        reason = (
            f"{payment_category} 업종에서 "
            f"{benefit_text} 혜택이 적용되며, "
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
    이번 달 실적 달성 상태를 계산합니다.
    """

    required = int(
        get_field(
            card,
            "required_spending",
            "실적조건",
            default=0,
        )
        or 0
    )

    current = int(get_current_month_spending(card))

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
def apply_benefit_limits(
    calculated_benefit: int | float,
    benefit: dict,
    benefit_used: int | float
) -> dict:
    """
    계산된 혜택금액에 회당 한도와
    혜택별 월 잔여한도를 적용합니다.
    """

    expected_benefit = max(
        float(calculated_benefit or 0),
        0
    )

    benefit_used = max(
        float(benefit_used or 0),
        0
    )

    # 1. 회당 할인한도
    per_transaction_limit = benefit.get(
        "한도_회당"
    )

    if per_transaction_limit is not None:
        expected_benefit = min(
            expected_benefit,
            float(per_transaction_limit)
        )

    # 2. 혜택별 월 최대 할인액
    monthly_benefit_limit = benefit.get(
        "월최대혜택액"
    )

    if monthly_benefit_limit is not None:
        remaining_monthly_limit = max(
            float(monthly_benefit_limit)
            - benefit_used,
            0
        )

        expected_benefit = min(
            expected_benefit,
            remaining_monthly_limit
        )
    else:
        remaining_monthly_limit = None

    return {
        "expected_benefit": int(expected_benefit),
        "per_transaction_limit": (
            int(per_transaction_limit)
            if per_transaction_limit is not None
            else None
        ),
        "monthly_benefit_limit": (
            int(monthly_benefit_limit)
            if monthly_benefit_limit is not None
            else None
        ),
        "benefit_used": int(benefit_used),
        "remaining_monthly_limit": (
            int(remaining_monthly_limit)
            if remaining_monthly_limit is not None
            else None
        )
    }


def get_temporary_monthly_cap(benefit: dict | object):
    temporary_cap = get_field(
        benefit,
        "임시월캡",
        "temporary_monthly_cap",
    )

    if temporary_cap is not None:
        return temporary_cap

    additional_conditions = get_field(
        benefit,
        "additional_conditions",
    )

    if isinstance(additional_conditions, dict):
        return get_field(
            additional_conditions,
            "임시월캡",
            "temporary_monthly_cap",
        )

    return None


def calculate_base_benefit(
    payment_amount: int,
    benefit: dict | object,
) -> float:
    """혜택 단위에 따라 한도 적용 전 기본 혜택액을 계산합니다."""

    benefit_value = to_non_negative_float(
        get_field(
            benefit,
            "혜택값",
            "benefit_value",
        )
    )
    benefit_unit = get_field(
        benefit,
        "혜택단위",
        "benefit_unit",
    )

    if benefit_value is None:
        return 0

    if benefit_unit == "%":
        return max(payment_amount, 0) * benefit_value / 100

    if benefit_unit in {"원", "KRW"}:
        # A fixed discount cannot be larger than the transaction itself.
        return min(max(payment_amount, 0), benefit_value)

    return 0


def get_previous_month_spending(card: dict | object) -> float:
    return (
        to_non_negative_float(
            get_field(
                card,
                "previous_month_spending",
                "previous_month_spend",
                "전월실적사용액",
                default=0,
            )
        )
        or 0
    )


def get_current_month_spending(card: dict | object) -> float:
    return (
        to_non_negative_float(
            get_field(
                card,
                "current_month_spending",
                "current_month_spend",
                "당월실적사용액",
                default=0,
            )
        )
        or 0
    )


def get_benefit_usage_this_month(
    card: dict | object,
    source_benefit_id,
) -> float:
    """혜택 ID별 이번 달 사용액을 읽습니다."""

    for field_name in (
        "benefit_usage_this_month",
        "benefit_usage",
    ):
        usage = get_field(card, field_name)

        if isinstance(usage, dict):
            value = usage.get(source_benefit_id)

            if value is None and source_benefit_id is not None:
                value = usage.get(str(source_benefit_id))

            if isinstance(value, dict):
                value = get_field(
                    value,
                    "monthly_used_amount",
                    "monthly_used",
                    "monthly_benefit_used",
                    default=0,
                )

            return to_non_negative_float(value) or 0

    return 0


def get_card_monthly_benefit_used(
    card: dict | object,
) -> float:
    """카드 전체의 이번 달 누적 혜택 사용액을 읽습니다."""

    usage = get_field(
        card,
        "monthly_card_usage",
        "card_benefit_usage",
        "card_monthly_benefit_used",
        "monthly_benefit_used",
        default=0,
    )

    if isinstance(usage, dict):
        return sum(
            to_non_negative_float(value) or 0
            for value in usage.values()
        )

    return to_non_negative_float(usage) or 0


def calculate_scored_benefit(
    card: dict | object,
    benefit: dict | object,
    payment_amount: int,
    benefit_used: int | float = 0,
) -> dict:
    """A/B 등급 정책에 따라 예상 혜택과 적용 한도를 계산합니다."""

    scoring_grade = get_scoring_grade(benefit) or "A_확정계산"
    is_estimated = scoring_grade == "B_추정계산"
    required_spending = to_non_negative_float(
        get_field(
            benefit,
            "실적조건",
            "required_spending",
        )
    )
    previous_month_spending = get_previous_month_spending(card)
    performance_met = (
        required_spending in (None, 0)
        or previous_month_spending >= required_spending
    )
    benefit_used_value = (
        to_non_negative_float(benefit_used) or 0
    )
    monthly_benefit_limit = to_non_negative_float(
        get_field(
            benefit,
            "월최대혜택액",
            "monthly_benefit_limit",
            "monthly_limit",
        )
    )
    monthly_remaining = (
        max(monthly_benefit_limit - benefit_used_value, 0)
        if monthly_benefit_limit is not None
        else None
    )
    usage_fields = {
        "required_spending": (
            int(required_spending)
            if required_spending is not None
            else None
        ),
        "previous_month_spending": int(previous_month_spending),
        "performance_met": performance_met,
        "monthly_limit": (
            int(monthly_benefit_limit)
            if monthly_benefit_limit is not None
            else None
        ),
        "monthly_used": int(benefit_used_value),
        "monthly_remaining": (
            int(monthly_remaining)
            if monthly_remaining is not None
            else None
        ),
    }

    if (
        should_exclude_from_calculation(benefit)
        or scoring_grade in EXCLUDED_SCORING_GRADES
    ):
        exclusion_reason = (
            get_exclusion_reason(benefit)
            or f"{scoring_grade} 등급은 추천 금액 계산에서 제외"
        )
        return {
            "expected_benefit": 0,
            "scoring_grade": scoring_grade,
            "is_estimated": False,
            "calculation_reason": exclusion_reason,
            "applied_cap": None,
            **usage_fields,
        }

    if not performance_met:
        return {
            "expected_benefit": 0,
            "scoring_grade": scoring_grade,
            "is_estimated": is_estimated,
            "calculation_reason": (
                "전월실적 미달: "
                f"필요 {int(required_spending or 0):,}원, "
                f"현재 {int(previous_month_spending):,}원"
            ),
            "applied_cap": None,
            **usage_fields,
        }

    base_benefit = calculate_base_benefit(
        payment_amount,
        benefit,
    )
    card_benefit_used = get_card_monthly_benefit_used(card)

    per_transaction_limit = to_non_negative_float(
        get_field(
            benefit,
            "한도_회당",
            "per_transaction_limit",
        )
    )
    card_total_limit = to_non_negative_float(
        get_field(
            card,
            "통합한도_월",
            "monthly_total_limit",
        )
    )
    temporary_monthly_cap = to_non_negative_float(
        get_temporary_monthly_cap(benefit)
    )

    cap_candidates: list[tuple[str, float]] = []

    if per_transaction_limit is not None:
        cap_candidates.append(
            ("회당 한도", per_transaction_limit)
        )

    if monthly_benefit_limit is not None:
        cap_candidates.append(
            (
                "월최대혜택액 잔여한도",
                monthly_remaining or 0,
            )
        )

    if card_total_limit is not None:
        cap_candidates.append(
            (
                "카드 통합 잔여한도",
                max(
                    card_total_limit - card_benefit_used,
                    0,
                ),
            )
        )

    if is_estimated and temporary_monthly_cap is not None:
        cap_candidates.append(
            (
                "임시월캡 잔여한도",
                max(
                    temporary_monthly_cap - benefit_used_value,
                    0,
                ),
            )
        )

    if is_estimated and not cap_candidates:
        return {
            "expected_benefit": 0,
            "scoring_grade": scoring_grade,
            "is_estimated": True,
            "calculation_reason": "B등급 한도 확인 필요",
            "applied_cap": None,
            **usage_fields,
        }

    if cap_candidates:
        cap_name, applied_cap = min(
            cap_candidates,
            key=lambda item: item[1],
        )
        expected_benefit = min(base_benefit, applied_cap)
        if (
            monthly_remaining == 0
            and cap_name == "월최대혜택액 잔여한도"
        ):
            calculation_reason = "월 혜택 한도 소진"
        elif (
            card_total_limit is not None
            and card_total_limit - card_benefit_used <= 0
            and cap_name == "카드 통합 잔여한도"
        ):
            calculation_reason = "카드 통합한도 소진"
        else:
            calculation_reason = (
                f"기본 혜택 {int(base_benefit):,}원에 "
                f"{cap_name} {int(applied_cap):,}원 적용"
            )
    else:
        applied_cap = None
        expected_benefit = base_benefit
        calculation_reason = (
            f"기본 혜택 {int(base_benefit):,}원 계산"
        )

    if is_estimated:
        calculation_reason = "B등급 추정계산: " + calculation_reason
    else:
        calculation_reason = "A등급 확정계산: " + calculation_reason

    return {
        "expected_benefit": int(max(expected_benefit, 0)),
        "scoring_grade": scoring_grade,
        "is_estimated": is_estimated,
        "calculation_reason": calculation_reason,
        "applied_cap": (
            int(applied_cap)
            if applied_cap is not None
            else None
        ),
        **usage_fields,
    }


def calculate_card_benefit(
    card: dict,
    payment_category: str,
    payment_amount: int,
    merchant_name: str | None = None,
) -> dict:
    """
    Calculate the benefit for a given card and payment details.
    """
    applicable_benefits = []
    failure_reasons = []
    failure_calculation = None

    performance_status = calculate_performance_status(
    card=card,
    payment_amount=payment_amount
)

    for benefit in card["benefits"]:

        is_conditional = False
        caveats = []
        item_caveat = get_item_caveat(benefit)
        if item_caveat:
            caveats.append(item_caveat)

        option_metadata = get_option_metadata(benefit)

        if should_exclude_from_calculation(benefit):
            if failure_calculation is None:
                failure_calculation = calculate_scored_benefit(
                    card=card,
                    benefit=benefit,
                    payment_amount=payment_amount,
                )
                failure_calculation.update(option_metadata)
                failure_calculation["option_selected"] = False
                failure_calculation[
                    "option_selection_reason"
                ] = (
                    "옵션헤더"
                    if is_option_header(benefit)
                    else "계산 제외 혜택"
                )
            continue

        benefit_id = get_field(
            benefit,
            "혜택ID",
            "source_benefit_id",
            "benefit_id",
        )

        benefit_used = get_benefit_usage_this_month(
            card,
            benefit_id,
        )

        benefit_type = get_field(
            benefit,
            "혜택유형",
            "benefit_type",
        )

        if benefit_type != "할인":
            continue

        benefit_unit = get_field(
            benefit,
            "혜택단위",
            "benefit_unit",
        )

        if benefit_unit not in {"%", "원", "KRW"}:
            continue

        if not is_category_matched(
            benefit,
            payment_category
        ):
            continue

        if should_use_llm(benefit) and merchant_name:
            try:
                judgment = judge_ambiguous_benefit(
                    merchant_name=merchant_name,
                    payment_category=payment_category,
                    payment_amount=payment_amount,
                    benefit_name=get_field(
                        benefit,
                        "benefit_name",
                        "혜택명",
                        default="혜택명 없음",
                    ),
                    benefit_rule=get_benefit_rule_text(benefit),
                )

            except LLMServiceError:
                logger.exception(
                    "LLM benefit judgment failed",
                    extra={
                        "benefit_id": benefit_id,
                        "merchant_name": merchant_name,
                    },
                )
                is_conditional = True
                caveats.append(
                    "AI 판단 오류로 세부 적용 여부 확인이 필요합니다."
                )

            else:
                if judgment.needs_human_review:
                    is_conditional = True
                    caveats.append(judgment.caveat or judgment.reason)

                if not judgment.applicable and not judgment.needs_human_review:
                    failure_reasons.append(
                        f"혜택 적용 불가: {judgment.reason}"
                    )
                    continue

        calculation = calculate_scored_benefit(
            card=card,
            benefit=benefit,
            payment_amount=payment_amount,
            benefit_used=benefit_used,
        )
        expected_benefit = calculation["expected_benefit"]
        required_spending = calculation["required_spending"]

        if expected_benefit <= 0:
            calculation.update(option_metadata)
            calculation["option_selected"] = False
            calculation["option_selection_reason"] = (
                "계산 제외 옵션"
                if option_metadata["is_option_benefit"]
                else "일반 혜택"
            )
            failure_calculation = calculation
            failure_reasons.append(
                calculation["calculation_reason"]
            )
            continue

        display_fields = get_benefit_display_fields(benefit)

        applicable_benefits.append({
            "benefit_id": benefit_id,
            "expected_benefit": expected_benefit,
            "benefit_rate": get_field(
                benefit,
                "혜택값",
                "benefit_value",
            ),
            "benefit_unit": benefit_unit,
            "eligible": True,
            "is_conditional": is_conditional,
            "caveat": " ".join(dict.fromkeys(caveats)) or None,
            **display_fields,
            **option_metadata,
            **{
                key: calculation[key]
                for key in (
                    "scoring_grade",
                    "is_estimated",
                    "calculation_reason",
                    "applied_cap",
                    "required_spending",
                    "previous_month_spending",
                    "performance_met",
                    "monthly_limit",
                    "monthly_used",
                    "monthly_remaining",
                )
            },
        })

    applicable_benefits = select_option_candidates(
        card,
        applicable_benefits,
    )

    if not applicable_benefits:
        reason = (
            failure_reasons[0]
            if failure_reasons
            else "현재 결제 업종에 적용 가능한 혜택이 없습니다."
        )

        calculation_fields = failure_calculation or {
            "scoring_grade": None,
            "is_estimated": False,
            "calculation_reason": reason,
            "applied_cap": None,
            "required_spending": None,
            "previous_month_spending": int(
                get_previous_month_spending(card)
            ),
            "performance_met": True,
            "monthly_limit": None,
            "monthly_used": 0,
            "monthly_remaining": None,
            "option_group": None,
            "is_option_benefit": False,
            "option_selected": False,
            "option_selection_reason": "일반 혜택",
        }

        return {
            "card_id": card["card_id"],
            "card_name": card["card_name"],
            "card_company": card["card_company"],
            "card_image": card["card_image"],
            "last_four": card.get("card_number_last4"),
            "expected_benefit": 0,
            "eligible": False,
            "is_conditional": False,
            "caveat": None,
            "reason": reason,
            "reason_details": [reason, "예상 혜택 0원"],
            "scoring_grade": calculation_fields[
                "scoring_grade"
            ],
            "is_estimated": calculation_fields[
                "is_estimated"
            ],
            "calculation_reason": calculation_fields[
                "calculation_reason"
            ],
            "applied_cap": calculation_fields["applied_cap"],
            "required_spending": calculation_fields[
                "required_spending"
            ],
            "previous_month_spending": calculation_fields[
                "previous_month_spending"
            ],
            "performance_met": calculation_fields[
                "performance_met"
            ],
            "monthly_limit": calculation_fields[
                "monthly_limit"
            ],
            "monthly_used": calculation_fields["monthly_used"],
            "monthly_remaining": calculation_fields[
                "monthly_remaining"
            ],
            "monthly_transaction_count": int(
                card.get("monthly_transaction_count", 0) or 0
            ),
            "current_month_spending": int(
                card.get("current_month_spending", 0) or 0
            ),
            "option_group": calculation_fields.get(
                "option_group"
            ),
            "is_option_benefit": calculation_fields.get(
                "is_option_benefit",
                False,
            ),
            "option_selected": calculation_fields.get(
                "option_selected",
                False,
            ),
            "option_selection_reason": calculation_fields.get(
                "option_selection_reason",
                "일반 혜택",
            ),
            **performance_status
        }

    best_benefit = max(
        applicable_benefits,
        key=lambda item: (
            not item.get("is_conditional", False),
            item["expected_benefit"],
        ),
    )


    reason, reason_details = build_recommendation_reason(
        payment_category=payment_category,
        benefit_rate=best_benefit["benefit_rate"],
        expected_benefit=best_benefit["expected_benefit"],
        required_spending=best_benefit["required_spending"],
        previous_month_spending=card[
            "previous_month_spending"
        ],
        benefit_unit=best_benefit["benefit_unit"],
    )
    reason, reason_details = build_success_reason(
        payment_category=payment_category,
        benefit_rate=best_benefit["benefit_rate"],
        expected_benefit=best_benefit["expected_benefit"],
        benefit_unit=best_benefit["benefit_unit"],
    )
    if best_benefit["is_conditional"]:
        reason_details.append("적용 여부 확인 필요")
        if best_benefit["caveat"]:
            reason_details.append(best_benefit["caveat"])

    return {
        "card_id": card["card_id"],
        "card_name": card["card_name"],
        "card_company": card["card_company"],
        "card_image": card["card_image"],
        "last_four": card.get("card_number_last4"),
        "expected_benefit": best_benefit[
            "expected_benefit"
        ],
        "eligible": True,
        "is_conditional": best_benefit["is_conditional"],
        "caveat": best_benefit["caveat"],
        "benefit_rate": best_benefit["benefit_rate"],
        "benefit_unit": best_benefit["benefit_unit"],
        "reason": reason,
        "reason_details": reason_details,
        "benefit_name": best_benefit["benefit_name"],
        "summary": best_benefit["summary"],
        "detail": best_benefit["detail"],
        "benefit_summary": best_benefit["summary"],
        "scoring_grade": best_benefit["scoring_grade"],
        "is_estimated": best_benefit["is_estimated"],
        "calculation_reason": best_benefit[
            "calculation_reason"
        ],
        "applied_cap": best_benefit["applied_cap"],
        "required_spending": best_benefit["required_spending"],
        "previous_month_spending": best_benefit[
            "previous_month_spending"
        ],
        "performance_met": best_benefit["performance_met"],
        "monthly_limit": best_benefit["monthly_limit"],
        "monthly_used": best_benefit["monthly_used"],
        "monthly_remaining": best_benefit[
            "monthly_remaining"
        ],
        "monthly_transaction_count": int(
            card.get("monthly_transaction_count", 0) or 0
        ),
        "current_month_spending": int(
            card.get("current_month_spending", 0) or 0
        ),
        "option_group": best_benefit["option_group"],
        "is_option_benefit": best_benefit[
            "is_option_benefit"
        ],
        "option_selected": best_benefit["option_selected"],
        "option_selection_reason": best_benefit[
            "option_selection_reason"
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
    # 4. 해당 월에 자주 사용한 카드
    # 5. 해당 월 사용금액이 큰 카드
    # 6. 현재 달성률이 높은 카드
    # 7. 예상 혜택이 큰 카드
    return (
        not (
            required > 0
            and needs_performance
        ),
        not reaches_target,
        remaining_after,
        -card.get("monthly_transaction_count", 0),
        -card.get("current_month_spending", 0),
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

    # 최고 혜택 카드와 예상 혜택이 정확히 같은 카드들
    similar_cards = [
        card
        for card in benefit_sorted
        if card["expected_benefit"] == best_benefit
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
    payment_amount: int,
    user_card_states: list[dict],
) -> dict:
    """
    사용자의 모든 보유카드를 비교하고 추천 순위를 반환합니다.

    추천 기준:
    1. 혜택 차이가 크면 예상 혜택이 큰 카드 추천
    2. 예상 혜택이 동일하면 실적 달성에 유리한 카드 추천
    3. 모든 카드 혜택이 0원이면 실적 달성에 유리한 카드 추천
    """

    user_cards = user_card_states
    results = []

    # 1. 보유카드별 예상 혜택 계산
    for card in user_cards:
        card_result = calculate_card_benefit(
    card=card,
    merchant_name=merchant_name,
    payment_category=payment_category,
    payment_amount=payment_amount,
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
            "performance_prompt": None,
            "selection_required": False,
            "selectable_cards": [],
            "other_cards": [],
            "comparison": []
        }

    # 2. 확정 혜택을 우선하고, 같은 상태에서는 예상 혜택 순으로 정렬
    results.sort(
        key=lambda item: (
            item.get("is_conditional", False),
            -item["expected_benefit"],
        )
    )
    best_benefit_amount = results[0][
        "expected_benefit"
    ]

    performance_eligible_cards = [
        card
        for card in results
        if (
            card.get("performance_required", 0) > 0
            and card.get("needs_performance", False)
        )
    ]

    if best_benefit_amount <= 0 and not performance_eligible_cards:
        for index, card in enumerate(results, start=1):
            card["rank"] = index
            card["is_recommended"] = False
            card["difference_from_best_benefit"] = 0
            card["ranking_reason"] = "현재 거래에서 적용 가능한 혜택 없음"

        message = "혜택이 적용되는 카드가 없습니다. 원하시는 카드로 결제하세요."
        return {
            "transaction": {
                "merchant_name": merchant_name,
                "category": payment_category,
                "amount": payment_amount,
            },
            "recommendation_basis": "user_selection",
            "recommended_card": None,
            "additional_saving": 0,
            "saving_message": message,
            "performance_prompt": None,
            "selection_required": True,
            "selectable_cards": results,
            "other_cards": results,
            "comparison": results,
        }

    # 3. 최종 추천 카드 결정
    if best_benefit_amount <= 0:
        # 모든 카드 혜택이 0원
        recommended_card = select_card_by_performance(
            results
        )

        recommendation_basis = "performance_only"

    elif len(results) >= 2:
        # 예상 혜택이 정확히 같은 카드만 실적 기준으로 비교
        same_benefit_cards = [
            card
            for card in results
            if (
                card["expected_benefit"] == best_benefit_amount
                and card.get("is_conditional", False)
                == results[0].get("is_conditional", False)
            )
        ]

        if len(same_benefit_cards) >= 2:
            recommended_card = select_card_by_performance(
                same_benefit_cards
            )
            recommendation_basis = "performance_tiebreak"
        else:
            recommended_card = results[0]
            recommendation_basis = "benefit"

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
                    "이번 달 실적 달성에 가장 유리한 "
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
                "카드별 예상 혜택이 동일하여, "
                "이번 달 실적 달성에 더 유리한 "
                "카드를 추천합니다."
            )

            recommended_card["reason_details"] = [
                "동일한 예상 혜택의 카드 중 선정",
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
            if card.get("is_conditional", False):
                card["ranking_reason"] += " · 적용 여부 확인 필요"

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
            "예상 혜택이 동일하여 "
            "이번 달 실적 달성에 유리한 카드를 추천했습니다."
        )

    else:
        saving_message = (
            "적용 가능한 즉시 혜택이 없어 "
            "이번 달 실적 달성에 유리한 카드를 추천했습니다."
        )

    performance_candidates = [
        card
        for card in results
        if (
            card.get("reaches_target_with_payment", False)
            and card["card_id"] != recommended_card_id
        )
    ]
    performance_card = select_card_by_performance(
        performance_candidates
    )
    performance_prompt = None
    if performance_card is not None:
        remaining = performance_card.get(
            "performance_remaining_before",
            0,
        )
        performance_prompt = {
            "card_id": performance_card["card_id"],
            "card_name": performance_card["card_name"],
            "remaining_before_payment": remaining,
            "message": (
                f"{performance_card['card_name']}은(는) 실적 달성까지 "
                f"{remaining:,}원 남았습니다. 이번 결제로 실적을 "
                "달성할 수 있습니다. 이 카드로 결제하시겠습니까?"
            ),
            "action_label": "예",
        }

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
        "performance_prompt": performance_prompt,
        "selection_required": False,
        "selectable_cards": [],
        "other_cards": other_cards,
        "comparison": results
    }


if __name__ == "__main__":
    recommendation = recommend_cards(
    user_card_states=[],
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
