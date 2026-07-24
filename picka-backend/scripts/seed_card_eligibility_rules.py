from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import delete, select

from app.core.database import SessionLocal
from app.models import Card, CardEligibilityRule, CardRecommendationSnapshot


@dataclass(frozen=True)
class RuleDefinition:
    eligibility_type: str
    required_value: str
    comparison_operator: str = "EQ"
    description: str = ""


EXACT_SOURCE_CARD_IDS: dict[int, tuple[RuleDefinition, ...]] = {
    **{
        card_id: (RuleDefinition("MILITARY_SERVICE", "true", description="병역 대상자 전용 카드"),)
        for card_id in (446, 739, 2933, 2934, 2941)
    },
    **{
        card_id: (RuleDefinition("STUDENT", "true", description="학생 신분 확인 필요"),)
        for card_id in (1610, 1615, 1616, 1617, 1618, 1619)
    },
    **{
        card_id: (RuleDefinition("AGE_GROUP", "TEEN", description="청소년·유스 연령 조건 확인 필요"),)
        for card_id in (760, 1298, 2314, 2929)
    },
    1816: (RuleDefinition("AGE_GROUP", "SENIOR", description="시니어 연령 조건 확인 필요"),),
    1451: (
        RuleDefinition(
            "FOREIGNER", "true",
            description="만 18세 이상 외국인 대상 카드",
        ),
        RuleDefinition("AGE", "18", comparison_operator="GTE", description="만 18세 이상"),
    ),
    2917: (
        RuleDefinition(
            "FOREIGNER",
            "true",
            description="외국인 실명확인증표 보유 외국인 대상 카드",
        ),
        RuleDefinition("AGE", "7", comparison_operator="GTE", description="만 7세 이상"),
    ),
    2919: (
        RuleDefinition(
            "FOREIGNER", "true",
            description="만 18세 이상 국내 거주 외국인 대상 카드",
        ),
        RuleDefinition("AGE", "18", comparison_operator="GTE", description="만 18세 이상"),
    ),
    2921: (
        RuleDefinition(
            "FOREIGNER", "true",
            description="외국인등록증 소지 외국인 대상 카드",
        ),
        RuleDefinition("AGE", "12", comparison_operator="GTE", description="만 12세 이상"),
    ),
    2922: (
        RuleDefinition(
            "FOREIGNER", "true",
            description="외국인등록증 소지 외국인 대상 카드",
        ),
        RuleDefinition("AGE", "12", comparison_operator="GTE", description="만 12세 이상"),
    ),
    685: (
        RuleDefinition(
            "AGE_GROUP", "TEEN",
            description="만 12세~18세 청소년 전용 카드",
        ),
    ),
    **{
        card_id: (RuleDefinition("BUSINESS_OWNER", "true", description="개인사업자 전용 카드"),)
        for card_id in (2420, 2421)
    },
    **{
        card_id: (
            RuleDefinition("COMPACT_CAR_OWNER", "true", description="경차 보유 조건 확인 필요"),
            RuleDefinition("VEHICLE_OWNER", "true", description="차량 보유 조건 확인 필요"),
        )
        for card_id in (207, 303, 421, 854, 859, 2197, 2903)
    },
}

CHILDCARE_CARD_NAME_MARKERS = ("국민행복", "아이행복")
CHILDCARE_RULE = RuleDefinition(
    "PREGNANCY_CHILDCARE_SUPPORT_ELIGIBLE",
    "true",
    description="임신·출산·육아 지원카드 대상자",
)
MULTI_CHILD_CARD_NAME_MARKERS = ("다둥이 행복",)
MULTI_CHILD_RULE = RuleDefinition(
    "CHILDREN_COUNT",
    "2",
    comparison_operator="GTE",
    description="다자녀 가구(자녀 2명 이상) 대상 카드",
)


def _partner_rules(card_name: str) -> list[RuleDefinition]:
    upper_name = card_name.upper()
    lower_name = card_name.lower()

    if "하이패스" in card_name:
        return [
            RuleDefinition("HIGHPASS_USER", "true", description="하이패스 이용자 대상 카드"),
            RuleDefinition("VEHICLE_OWNER", "true", description="차량 보유 조건 확인 필요"),
        ]
    if "K-패스" in card_name or "K패스" in card_name or "알뜰교통" in card_name:
        return [RuleDefinition("KPASS_USER", "true", description="K-패스·교통정책 이용 확인 필요")]
    if "SKT" in upper_name:
        return [RuleDefinition("TELECOM_PROVIDER", "SKT", description="SKT 제휴카드")]
    if "LG U+" in upper_name:
        return [RuleDefinition("TELECOM_PROVIDER", "LGU+", description="LG U+ 제휴카드")]
    if "kt wiz" not in lower_name and (
        lower_name.startswith("kt ")
        or " kt " in lower_name
        or lower_name.startswith("kt-")
        or "kt m mobile" in lower_name
    ):
        return [RuleDefinition("TELECOM_PROVIDER", "KT", description="KT 제휴카드")]
    if "대한항공" in card_name:
        return [RuleDefinition("PREFERRED_AIRLINE", "KOREAN_AIR", description="대한항공 제휴카드")]
    if "아시아나" in card_name:
        return [RuleDefinition("PREFERRED_AIRLINE", "ASIANA", description="아시아나 제휴카드")]
    if any(marker in card_name for marker in ("롯데백화점", "롯데마트", "롯데면세점", "하이마트")):
        return [RuleDefinition("PRIMARY_SHOPPING_AFFILIATION", "LOTTE", description="롯데 쇼핑 제휴카드")]
    if any(marker in card_name for marker in ("이마트", "이마트에브리데이")):
        return [RuleDefinition("PRIMARY_SHOPPING_AFFILIATION", "EMART", description="이마트 쇼핑 제휴카드")]
    if any(marker in card_name for marker in ("신세계백화점", "신세계면세점")):
        return [RuleDefinition("PRIMARY_SHOPPING_AFFILIATION", "SHINSEGAE", description="신세계 쇼핑 제휴카드")]
    return []


def main() -> None:
    inserted = 0
    updated = 0

    with SessionLocal() as db:
        cards = db.scalars(select(Card)).all()
        cards_by_source_id = {card.source_card_id: card for card in cards}
        missing = sorted(set(EXACT_SOURCE_CARD_IDS) - set(cards_by_source_id))
        if missing:
            raise RuntimeError(f"DB에 없는 source_card_id: {missing}")

        definitions: dict[tuple[int, str], RuleDefinition] = {}
        for source_card_id, rules in EXACT_SOURCE_CARD_IDS.items():
            card = cards_by_source_id[source_card_id]
            for rule in rules:
                definitions[(card.id, rule.eligibility_type)] = rule

        for card in cards:
            if any(marker in card.card_name for marker in CHILDCARE_CARD_NAME_MARKERS):
                definitions[(card.id, CHILDCARE_RULE.eligibility_type)] = CHILDCARE_RULE
            if any(marker in card.card_name for marker in MULTI_CHILD_CARD_NAME_MARKERS):
                definitions[(card.id, MULTI_CHILD_RULE.eligibility_type)] = MULTI_CHILD_RULE
            for rule in _partner_rules(card.card_name):
                definitions[(card.id, rule.eligibility_type)] = rule

        managed_types = {
            "MILITARY_SERVICE", "STUDENT", "AGE_GROUP", "BUSINESS_OWNER",
            "FOREIGNER", "AGE",
            "COMPACT_CAR_OWNER", "VEHICLE_OWNER",
            "PREGNANCY_CHILDCARE_SUPPORT_ELIGIBLE", "CHILDREN_COUNT",
            "HIGHPASS_USER", "KPASS_USER", "TELECOM_PROVIDER",
            "PREFERRED_AIRLINE", "PRIMARY_SHOPPING_AFFILIATION",
        }
        expected_keys = set(definitions)
        for old_rule in db.scalars(select(CardEligibilityRule)).all():
            if (
                old_rule.eligibility_type in managed_types
                and (old_rule.card_id, old_rule.eligibility_type) not in expected_keys
            ):
                db.delete(old_rule)

        for (card_id, eligibility_type), definition in definitions.items():
            rule = db.scalar(select(CardEligibilityRule).where(
                CardEligibilityRule.card_id == card_id,
                CardEligibilityRule.eligibility_type == eligibility_type,
            ))
            if rule is None:
                rule = CardEligibilityRule(card_id=card_id, eligibility_type=eligibility_type)
                db.add(rule)
                inserted += 1
            else:
                updated += 1
            rule.required_value = definition.required_value
            rule.comparison_operator = definition.comparison_operator
            rule.description = definition.description

        db.execute(delete(CardRecommendationSnapshot))
        db.commit()

    print(f"inserted={inserted}")
    print(f"updated={updated}")


if __name__ == "__main__":
    main()
