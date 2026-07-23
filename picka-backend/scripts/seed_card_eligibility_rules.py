from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Card, CardEligibilityRule


@dataclass(frozen=True)
class RuleDefinition:
    eligibility_type: str
    required_value: str
    comparison_operator: str = "EQ"
    description: str = ""


EXACT_SOURCE_CARD_IDS: dict[int, RuleDefinition] = {
    # 나라사랑카드
    **{
        card_id: RuleDefinition(
            "MILITARY_SERVICE", "true", description="병역 대상자 전용 카드"
        )
        for card_id in (446, 739, 2933, 2934, 2941)
    },
    # 학생증 카드
    **{
        card_id: RuleDefinition(
            "STUDENT", "true", description="학생 신분 확인 필요"
        )
        for card_id in (1610, 1615, 1616, 1617, 1618, 1619)
    },
    # 청소년·유스 카드
    **{
        card_id: RuleDefinition(
            "AGE_GROUP", "TEEN", description="청소년·유스 연령 조건 확인 필요"
        )
        for card_id in (760, 1298, 2314, 2929)
    },
    1816: RuleDefinition(
        "AGE_GROUP", "SENIOR", description="시니어 연령 조건 확인 필요"
    ),
    # 개인사업자 카드
    **{
        card_id: RuleDefinition(
            "BUSINESS_OWNER", "true", description="개인사업자 전용 카드"
        )
        for card_id in (2420, 2421)
    },
    # 경차·유류세 환급 카드
    **{
        card_id: RuleDefinition(
            "COMPACT_CAR_OWNER", "true", description="경차 보유 조건 확인 필요"
        )
        for card_id in (207, 303, 421, 854, 859, 2197, 2903)
    },
}

WELFARE_CARD_NAME_MARKERS = (
    "국민행복",
    "아이행복",
    "다둥이 행복",
)
WELFARE_RULE = RuleDefinition(
    "PREGNANCY_CHILDCARE_SUPPORT_ELIGIBLE",
    "true",
    description="정부 복지카드 지원 자격 확인 필요",
)


def _partner_rule(card_name: str) -> RuleDefinition | None:
    upper_name = card_name.upper()
    lower_name = card_name.lower()

    if "하이패스" in card_name:
        return RuleDefinition(
            "HIGHPASS_USER", "true", description="하이패스 이용자 대상 카드"
        )
    if "K-패스" in card_name or "K패스" in card_name or "알뜰교통" in card_name:
        return RuleDefinition(
            "KPASS_USER", "true", description="K-패스·교통정책 이용 확인 필요"
        )
    if "SKT" in upper_name:
        return RuleDefinition(
            "TELECOM_PROVIDER", "SKT", description="SKT 제휴카드"
        )
    if "LG U+" in upper_name:
        return RuleDefinition(
            "TELECOM_PROVIDER", "LGU+", description="LG U+ 제휴카드"
        )
    if "kt wiz" not in lower_name and (
        lower_name.startswith("kt ")
        or " kt " in lower_name
        or lower_name.startswith("kt-")
        or "kt m mobile" in lower_name
    ):
        return RuleDefinition(
            "TELECOM_PROVIDER", "KT", description="KT 제휴카드"
        )
    if "대한항공" in card_name:
        return RuleDefinition(
            "PREFERRED_AIRLINE", "KOREAN_AIR", description="대한항공 제휴카드"
        )
    if "아시아나" in card_name:
        return RuleDefinition(
            "PREFERRED_AIRLINE", "ASIANA", description="아시아나 제휴카드"
        )
    if any(
        marker in card_name
        for marker in ("롯데백화점", "롯데마트", "롯데면세점", "하이마트")
    ):
        return RuleDefinition(
            "PRIMARY_SHOPPING_AFFILIATION", "LOTTE", description="롯데 쇼핑 제휴카드"
        )
    if any(marker in card_name for marker in ("이마트", "이마트에브리데이")):
        return RuleDefinition(
            "PRIMARY_SHOPPING_AFFILIATION", "EMART", description="이마트 제휴카드"
        )
    if any(marker in card_name for marker in ("신세계백화점", "신세계면세점")):
        return RuleDefinition(
            "PRIMARY_SHOPPING_AFFILIATION",
            "SHINSEGAE",
            description="신세계 쇼핑 제휴카드",
        )
    return None


def main() -> None:
    inserted = 0
    updated = 0

    with SessionLocal() as db:
        cards = db.scalars(select(Card)).all()
        cards_by_source_id = {card.source_card_id: card for card in cards}
        missing = sorted(
            set(EXACT_SOURCE_CARD_IDS) - set(cards_by_source_id)
        )
        if missing:
            raise RuntimeError(f"DB에 없는 source_card_id: {missing}")

        definitions: dict[tuple[int, str], RuleDefinition] = {
            (
                cards_by_source_id[source_card_id].id,
                definition.eligibility_type,
            ): definition
            for source_card_id, definition in EXACT_SOURCE_CARD_IDS.items()
        }
        for card in cards:
            if any(marker in card.card_name for marker in WELFARE_CARD_NAME_MARKERS):
                definitions[(card.id, WELFARE_RULE.eligibility_type)] = WELFARE_RULE

            partner_rule = _partner_rule(card.card_name)
            if partner_rule is not None:
                definitions[
                    (card.id, partner_rule.eligibility_type)
                ] = partner_rule

        managed_descriptions = {
            definition.description for definition in definitions.values()
        } | {"정부 복지카드 지원 자격 확인 필요"}
        expected_keys = {
            key for key in definitions
        }
        for old_rule in db.scalars(select(CardEligibilityRule)).all():
            if (
                old_rule.description in managed_descriptions
                and (old_rule.card_id, old_rule.eligibility_type)
                not in expected_keys
            ):
                db.delete(old_rule)

        for (card_id, eligibility_type), definition in definitions.items():
            rule = db.scalar(
                select(CardEligibilityRule).where(
                    CardEligibilityRule.card_id == card_id,
                    CardEligibilityRule.eligibility_type
                    == eligibility_type,
                )
            )
            if rule is None:
                rule = CardEligibilityRule(
                    card_id=card_id,
                    eligibility_type=definition.eligibility_type,
                    required_value=definition.required_value,
                    comparison_operator=definition.comparison_operator,
                    description=definition.description,
                )
                db.add(rule)
                inserted += 1
            else:
                rule.required_value = definition.required_value
                rule.comparison_operator = definition.comparison_operator
                rule.description = definition.description
                updated += 1

        db.commit()

    print(f"inserted={inserted}")
    print(f"updated={updated}")


if __name__ == "__main__":
    main()
