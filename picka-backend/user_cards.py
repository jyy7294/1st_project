import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
CARD_DATABASE_PATH = BASE_DIR / "card_database.json"


# 가상 사용자가 보유한 실제 카드 상품 번호
USER_CARD_IDS = [13, 2262, 2261]


# 카드 상품 DB에는 없는 사용자별 가상 상태
USER_CARD_STATUS = {
    13: {
        "user_card_id": 1,
        "last_four": "1234",
        "nickname": "생활비 카드",
        "previous_month_spending": 450000,
        "monthly_benefit_used": 2000, # 사용자가 이번 달에 사용한 혜택 금액, 카드 전체 할인 사용량

        # 추가
        "benefit_usage": {}
    },
    2262: {
        "user_card_id": 2,
        "last_four": "5678",
        "nickname": "카페·외식 카드",
        "previous_month_spending": 500000,
        "monthly_benefit_used": 4000,

        # 추가
        "benefit_usage": {}
    },
    2261: {
        "user_card_id": 3,
        "last_four": "9012",
        "nickname": "기본 할인 카드",
        "previous_month_spending": 150000,
        "monthly_benefit_used": 0,

        # 추가
        "benefit_usage": {}
    }
}


def load_card_database() -> list[dict]:
    """전체 카드 데이터베이스를 불러옵니다."""

    try:
        with open(
            CARD_DATABASE_PATH,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

    except FileNotFoundError as error:
        raise FileNotFoundError(
            f"카드 데이터 파일이 없습니다: {CARD_DATABASE_PATH}"
        ) from error

    except json.JSONDecodeError as error:
        raise ValueError(
            "card_database.json 형식이 올바르지 않습니다."
        ) from error

    return data["cards"]

# 선택 카드 조회 함수 
def get_user_cards() -> list[dict]:
    """가상 사용자가 보유한 카드 목록을 반환합니다."""

    all_cards = load_card_database()
    result = []

    for card in all_cards:
        card_id = card["카드번호"]

        if card_id not in USER_CARD_IDS:
            continue

        user_status = USER_CARD_STATUS[card_id]

        result.append({
            "user_card_id": user_status["user_card_id"],
            "card_id": card_id,
            "card_company": card["카드사"],
            "card_name": card["카드명"],
            "card_image": card["카드이미지"],
            "last_four": user_status["last_four"],
            "nickname": user_status["nickname"],
            "previous_month_spending": user_status[
                "previous_month_spending"
            ],
            "required_spending": card.get("전월실적", 0) or 0,
            "monthly_benefit_used": user_status[
                "monthly_benefit_used"
            ],
            "card_monthly_benefit_used": user_status[
                "monthly_benefit_used"
            ],
            "monthly_total_limit": card.get("통합한도_월"),
            "benefits": card.get("혜택", []),
            "benefit_usage": user_status.get(
                "benefit_usage",
                {}
            ),
            "benefit_usage_this_month": user_status.get(
                "benefit_usage",
                {},
            ),
            "selected_option_group": user_status.get(
                "selected_option_group"
            ),
            "selected_option_benefit_id": user_status.get(
                "selected_option_benefit_id"
            ),
        })

    return result


def get_user_card_by_id(
    card_id: int
) -> dict | None:
    """카드 상품 번호로 사용자의 보유 카드를 조회합니다."""

    user_cards = get_user_cards()

    for card in user_cards:
        if card["card_id"] == card_id:
            return card

    return None


if __name__ == "__main__":
    user_cards = get_user_cards()

    print(f"보유카드 수: {len(user_cards)}장")

    for card in user_cards:
        print("-" * 50)
        print(f"카드번호: {card['card_id']}")
        print(f"카드명: {card['card_name']}")
        print(f"별칭: {card['nickname']}")
        print(f"끝 4자리: {card['last_four']}")
        print(
            f"전월 사용금액: "
            f"{card['previous_month_spending']:,}원"
        )
        print(f"혜택 개수: {len(card['benefits'])}개")
