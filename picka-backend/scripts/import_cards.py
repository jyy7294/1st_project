import json
import math
from pathlib import Path
from typing import Any

from app.models.card import Card
from app.models.card_benefit import CardBenefit


JSON_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "backend_recommendation_export.json"
)


def load_json(file_path: Path) -> Any:
    """JSON 파일을 읽어 Python 객체로 반환한다."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"JSON 파일을 찾을 수 없습니다.\n"
            f"확인한 경로: {file_path}"
        )

    with file_path.open(
        mode="r",
        # Accept both BOM-prefixed UTF-8 and regular UTF-8 JSON files.
        encoding="utf-8-sig",
    ) as file:
        return json.load(file)
    
def clean_value(value: Any) -> Any:
    """NaN 값을 None으로 변환한다."""

    if isinstance(value, float) and math.isnan(value):
        return None

    return value

def clean_nested_value(value: Any) -> Any:
    """dict와 list 내부의 NaN까지 모두 None으로 변환한다."""

    if isinstance(value, float) and math.isnan(value):
        return None

    if isinstance(value, dict):
        return {
            key: clean_nested_value(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            clean_nested_value(item)
            for item in value
        ]

    return value


def extract_cards(data: Any) -> list[dict[str, Any]]:
    """최상위 JSON 구조에서 카드 목록을 추출한다."""

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        cards = data.get("cards")

        if isinstance(cards, list):
            return cards

    raise ValueError(
        "카드 목록을 찾을 수 없습니다. "
        "JSON 최상위 구조를 다시 확인해 주세요."
    )


def create_card_model(card_data: dict[str, Any]) -> Card:
    """JSON 카드 데이터를 Card ORM 객체로 변환한다."""

    cleaned_card_data = clean_nested_value(card_data)

    return Card(
        source_card_id=clean_value(
            card_data.get("카드번호")
        ),
        card_name=card_data.get("카드명", ""),
        issuer=card_data.get("카드사"),
        card_type=card_data.get("구분"),
        annual_fee=clean_value(
            card_data.get("연회비_최소")
        ),
        previous_spending=clean_value(
            card_data.get("전월실적")
        ),
        monthly_total_limit=clean_value(
            card_data.get("통합한도_월")
        ),
        image_url=clean_value(
            card_data.get("이미지URL")
        ),
        source_url=clean_value(
            card_data.get("상세URL")
        ),
        raw_data=cleaned_card_data,
    )

def create_benefit_models(
    benefit_list: list[dict[str, Any]],
) -> list[CardBenefit]:
    """JSON 혜택 목록을 CardBenefit ORM 객체 목록으로 변환한다."""

    benefits: list[CardBenefit] = []

    for benefit_data in benefit_list:
        cleaned_benefit_data = clean_nested_value(
            benefit_data
        )

        additional_conditions = {
            "benefit_id": clean_value(
                benefit_data.get("혜택ID")
            ),
            "category_list": clean_value(
                benefit_data.get("카테고리목록")
            ),
            "weekday_condition": clean_value(
                benefit_data.get("요일조건")
            ),
            "time_condition": clean_value(
                benefit_data.get("시간조건")
            ),
            "merchant_level": clean_value(
                benefit_data.get("가맹점수준")
            ),
            "merchant_list": clean_value(
                benefit_data.get("가맹점목록")
            ),
            "scoring_grade": clean_value(
                benefit_data.get("스코어링등급")
            ),
            "warning_flag": clean_value(
                benefit_data.get("추천주의플래그")
            ),
            "temporary_monthly_cap": clean_value(
                benefit_data.get("임시월캡")
            ),
            "temporary_monthly_cap_source": clean_value(
                benefit_data.get("임시월캡_출처")
            ),
            "rule_parsing_confidence": clean_value(
                benefit_data.get("룰파싱신뢰도")
            ),
            "rule_review_required": clean_value(
                benefit_data.get("룰검수필요")
            ),
            "official_confirmation_status": clean_value(
                benefit_data.get("공식확인상태")
            ),
            "manual_correction_policy": clean_value(
                benefit_data.get("수동보정정책")
            ),
            "option_enabled": clean_value(
                benefit_data.get("옵션형")
            ),
            "option_group": clean_value(
                benefit_data.get("옵션그룹")
            ),
            "option_selection_method": clean_value(
                benefit_data.get("옵션선택방식")
            ),
            "option_change_cycle": clean_value(
                benefit_data.get("옵션변경주기")
            ),
            "option_combinable": clean_value(
                benefit_data.get("옵션합산가능여부")
            ),
            "option_rule_confidence": clean_value(
                benefit_data.get("옵션룰신뢰도")
            ),
        }

        benefit = CardBenefit(
            source_benefit_id=clean_value(
                benefit_data.get("혜택ID")
            ),
            benefit_name=clean_value(
                benefit_data.get("요약")
            ),
            category=clean_value(
                benefit_data.get("카테고리")
            ),
            benefit_type=clean_value(
                benefit_data.get("혜택유형")
            ),
            benefit_unit=clean_value(
                benefit_data.get("혜택단위")
            ),
            benefit_value=clean_value(
                benefit_data.get("혜택값")
            ),
            required_spending=clean_value(
                benefit_data.get("실적조건")
            ),
            minimum_payment=clean_value(
                benefit_data.get("최소결제금액")
            ),
            per_transaction_limit=clean_value(
                benefit_data.get("한도_회당")
            ),
            monthly_spending_limit=clean_value(
                benefit_data.get("한도_월")
            ),
            monthly_benefit_limit=clean_value(
                benefit_data.get("월최대혜택액")
            ),
            daily_count_limit=clean_value(
                benefit_data.get("횟수_일")
            ),
            monthly_count_limit=clean_value(
                benefit_data.get("횟수_월")
            ),
            annual_limit=clean_value(
                benefit_data.get("한도_연")
            ),
            limit_status=clean_value(
                benefit_data.get("한도상태")
            ),
            condition_text=clean_value(
                benefit_data.get("실적조건")
            ),
            exception_text=clean_value(
                benefit_data.get("제외조건목록")
            ),
            raw_text=clean_value(
                benefit_data.get("요약")
            ),
            source_summary=clean_value(
                benefit_data.get("요약")
            ),
            source_detail=clean_value(
                benefit_data.get("상세")
            ),
            additional_conditions=clean_nested_value(
                additional_conditions
            ),
            raw_data=cleaned_benefit_data,
        )

        benefits.append(benefit)

    return benefits

def main() -> None:
    data = load_json(JSON_PATH)

    cards = extract_cards(data)

    all_benefits = data.get("benefits", [])

    if not isinstance(all_benefits, list):
        raise ValueError(
            "'benefits' 데이터가 list 형태가 아닙니다."
        )

    print(f"전체 카드 개수: {len(cards)}")
    print(f"전체 혜택 개수: {len(all_benefits)}")

    if not cards:
        print("카드 데이터가 없습니다.")
        return

    first_card_data = cards[0]

    card_model = create_card_model(
        first_card_data
    )

    first_card_id = first_card_data.get(
        "카드번호"
    )

    benefit_list = [
        benefit
        for benefit in all_benefits
        if isinstance(benefit, dict)
        and benefit.get("카드번호")
        == first_card_id
    ]

    benefit_models = create_benefit_models(
        benefit_list
    )

    print("\n첫 번째 카드 변환 결과")
    print(
        "- source_card_id:",
        card_model.source_card_id,
    )
    print(
        "- card_name:",
        card_model.card_name,
    )
    print(
        "- issuer:",
        card_model.issuer,
    )
    print(
        "- card_type:",
        card_model.card_type,
    )
    print(
        "- annual_fee:",
        card_model.annual_fee,
    )
    print(
        "- previous_spending:",
        card_model.previous_spending,
    )
    print(
        "- monthly_total_limit:",
        card_model.monthly_total_limit,
    )

    print(
        "\n첫 번째 카드의 혜택 개수:",
        len(benefit_models),
    )

    if benefit_models:
        first_benefit = benefit_models[0]

        print("\n첫 번째 혜택 변환 결과")
        print(
            "- benefit_name:",
            first_benefit.benefit_name,
        )
        print(
            "- category:",
            first_benefit.category,
        )
        print(
            "- benefit_type:",
            first_benefit.benefit_type,
        )
        print(
            "- benefit_unit:",
            first_benefit.benefit_unit,
        )
        print(
            "- benefit_value:",
            first_benefit.benefit_value,
        )
        print(
            "- required_spending:",
            first_benefit.required_spending,
        )
        print(
            "- limit_status:",
            first_benefit.limit_status,
        )
        print(
            "- exception_text:",
            first_benefit.exception_text,
        )
        print(
            "- additional_conditions:",
            first_benefit.additional_conditions,
        )


if __name__ == "__main__":
    main()
