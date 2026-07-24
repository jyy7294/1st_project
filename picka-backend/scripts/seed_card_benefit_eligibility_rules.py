from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import CardBenefit, CardBenefitEligibilityRule


@dataclass(frozen=True)
class BenefitRuleDefinition:
    eligibility_type: str
    required_value: str
    comparison_operator: str
    description: str


MEMBERSHIP_PATTERNS = {
    "뷰티플렉스 멤버십": ("BEAUTYFLEX", "뷰티플렉스 멤버십 필요"),
    "위메프 회원": ("WEMAKEPRICE", "위메프 회원 가입 필요"),
    "토스 회원": ("TOSS", "토스 회원 가입 필요"),
    "롯데멤버스": ("LPOINT", "롯데멤버스·L.POINT 가입 필요"),
    "L.POINT 회원": ("LPOINT", "L.POINT 가입 필요"),
    "메리어트 본보이": ("MARRIOTT_BONVOY", "메리어트 본보이 가입 필요"),
    "오렌지카드 등록회원": ("E1_ORANGE", "E1 오렌지카드 등록 필요"),
    "T멤버십": ("T_MEMBERSHIP", "T멤버십 가입 필요"),
    "해피포인트 회원": ("HAPPYPOINT", "해피포인트 가입 필요"),
}

PROVIDER_PATTERNS = {
    "SKT 고객": ("TELECOM_PROVIDER", "SKT", "SKT 이용자 혜택"),
    "KT 고객": ("TELECOM_PROVIDER", "KT", "KT 이용자 혜택"),
    "LG U+ 고객": ("TELECOM_PROVIDER", "LGU+", "LG U+ 이용자 혜택"),
    "대한항공 스카이패스 회원": (
        "PREFERRED_AIRLINE",
        "KOREAN_AIR",
        "대한항공 스카이패스 가입 필요",
    ),
    "아시아나클럽 회원": (
        "PREFERRED_AIRLINE",
        "ASIANA",
        "아시아나클럽 가입 필요",
    ),
}


def _definitions(benefit: CardBenefit) -> list[BenefitRuleDefinition]:
    text = "\n".join(
        str(value)
        for value in (
            benefit.benefit_name,
            benefit.source_summary,
            benefit.source_detail,
            benefit.condition_text,
            benefit.exception_text,
        )
        if value
    )
    definitions = []
    for pattern, (membership, description) in MEMBERSHIP_PATTERNS.items():
        if pattern in text:
            definitions.append(BenefitRuleDefinition(
                "MEMBERSHIPS",
                membership,
                "CONTAINS",
                description,
            ))
    for pattern, (eligibility_type, value, description) in PROVIDER_PATTERNS.items():
        if pattern in text:
            definitions.append(BenefitRuleDefinition(
                eligibility_type,
                value,
                "EQ",
                description,
            ))
    return definitions


def main() -> None:
    inserted = 0
    updated = 0
    deleted = 0

    with SessionLocal() as db:
        benefits = db.scalars(select(CardBenefit)).all()
        expected: dict[tuple[int, str, str], BenefitRuleDefinition] = {}
        for benefit in benefits:
            for definition in _definitions(benefit):
                expected[
                    (
                        benefit.id,
                        definition.eligibility_type,
                        definition.required_value,
                    )
                ] = definition

        managed_descriptions = {
            definition.description for definition in expected.values()
        }
        for old_rule in db.scalars(select(CardBenefitEligibilityRule)).all():
            key = (
                old_rule.card_benefit_id,
                old_rule.eligibility_type,
                old_rule.required_value,
            )
            if old_rule.description in managed_descriptions and key not in expected:
                db.delete(old_rule)
                deleted += 1

        for key, definition in expected.items():
            benefit_id, eligibility_type, required_value = key
            rule = db.scalar(
                select(CardBenefitEligibilityRule).where(
                    CardBenefitEligibilityRule.card_benefit_id == benefit_id,
                    CardBenefitEligibilityRule.eligibility_type
                    == eligibility_type,
                    CardBenefitEligibilityRule.required_value == required_value,
                )
            )
            if rule is None:
                rule = CardBenefitEligibilityRule(
                    card_benefit_id=benefit_id,
                    eligibility_type=eligibility_type,
                    required_value=required_value,
                    comparison_operator=definition.comparison_operator,
                    description=definition.description,
                )
                db.add(rule)
                inserted += 1
            else:
                rule.comparison_operator = definition.comparison_operator
                rule.description = definition.description
                updated += 1

        db.commit()

    print(f"inserted={inserted}")
    print(f"updated={updated}")
    print(f"deleted={deleted}")


if __name__ == "__main__":
    main()
