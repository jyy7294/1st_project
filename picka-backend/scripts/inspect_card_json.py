import json
from pathlib import Path
from typing import Any


# 현재 파일:
# backend/scripts/inspect_card_json.py
#
# 확인할 JSON:
# backend/data/backend_recommendation_export.json
JSON_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "backend_recommendation_export.json"
)


def load_json(file_path: Path) -> Any:
    """JSON 파일을 읽어서 Python 객체로 반환한다."""

    if not file_path.exists():
        raise FileNotFoundError(
            f"JSON 파일을 찾을 수 없습니다.\n"
            f"확인한 경로: {file_path}"
        )

    with file_path.open(
        mode="r",
        # utf-8-sig removes a BOM when present and also reads normal UTF-8.
        encoding="utf-8-sig",
    ) as file:
        return json.load(file)


def main() -> None:
    data = load_json(JSON_PATH)

    print("=" * 60)
    print("JSON 파일 경로")
    print(JSON_PATH)
    print("=" * 60)

    print("최상위 자료형:", type(data).__name__)

    if isinstance(data, dict):
        print("최상위 키:", list(data.keys()))

        cards = data.get("cards")

        if cards is None:
            print("\n'cards' 키를 찾지 못했습니다.")
            print("실제 카드 목록이 들어 있는 키를 확인해야 합니다.")
            return

    elif isinstance(data, list):
        cards = data

    else:
        print("지원하지 않는 JSON 구조입니다.")
        return

    if not isinstance(cards, list):
        print("카드 데이터가 list 형태가 아닙니다.")
        print("현재 자료형:", type(cards).__name__)
        return

    print("카드 개수:", len(cards))

    if not cards:
        print("카드 데이터가 비어 있습니다.")
        return

    first_card = cards[0]

    if not isinstance(first_card, dict):
        print("첫 번째 카드가 dict 형태가 아닙니다.")
        return

    print("\n첫 번째 카드의 키:")
    for key in first_card.keys():
        print(f"- {key}")

    print("\n첫 번째 카드 일부:")
    print(
        json.dumps(
            first_card,
            ensure_ascii=False,
            indent=2,
        )[:3000]
    )

    benefits = data.get("benefits", [])

    print("\n" + "=" * 60)
    print("혜택 데이터 확인")
    print("=" * 60)

    print("혜택 자료형:", type(benefits).__name__)

    if isinstance(benefits, list):
        print("전체 혜택 개수:", len(benefits))

        if benefits:
            first_benefit = benefits[0]

            print("\n첫 번째 혜택의 키:")

            if isinstance(first_benefit, dict):
                for key in first_benefit.keys():
                    print(f"- {key}")

                print("\n첫 번째 혜택 일부:")
                print(
                    json.dumps(
                        first_benefit,
                        ensure_ascii=False,
                        indent=2,
                        allow_nan=True,
                    )
                )

    benefit_tiers = data.get("benefit_tiers", [])

    print("\n" + "=" * 60)
    print("혜택 구간 데이터 확인")
    print("=" * 60)

    print("혜택 구간 자료형:", type(benefit_tiers).__name__)

    if isinstance(benefit_tiers, list):
        print("전체 혜택 구간 개수:", len(benefit_tiers))

        if benefit_tiers:
            first_tier = benefit_tiers[0]

            print("\n첫 번째 혜택 구간의 키:")

            if isinstance(first_tier, dict):
                for key in first_tier.keys():
                    print(f"- {key}")

                print("\n첫 번째 혜택 구간 일부:")
                print(
                    json.dumps(
                        first_tier,
                        ensure_ascii=False,
                        indent=2,
                        allow_nan=True,
                    )
                )

    notice_benefits = [
        benefit
        for benefit in data.get("benefits", [])
        if isinstance(benefit, dict)
        and benefit.get("카테고리") == "유의사항"
    ]

    print("\n유의사항 데이터 개수:", len(notice_benefits))

    if notice_benefits:
        print("\n첫 번째 유의사항:")
        print(
            json.dumps(
                notice_benefits[0],
                ensure_ascii=False,
                indent=2,
                allow_nan=True,
            )
        )

if __name__ == "__main__":
    main()
