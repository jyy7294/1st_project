"""Read-only audit of benefit display risks for every active user card."""

from collections import Counter, defaultdict
import re

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import SessionLocal
from app.models import Card, CardBenefit, User, UserCard


SPENDING_CONDITION_PATTERN = re.compile(
    r"(?:전월|연간|1차년도|2차년도|이용\s*금액).{0,40}(?:만원|원).{0,20}(?:이상|충족)"
)


def main() -> None:
    with SessionLocal() as db:
        user_cards = list(
            db.scalars(
                select(UserCard)
                .where(UserCard.is_active.is_(True))
                .options(
                    selectinload(UserCard.card).selectinload(Card.benefits),
                    selectinload(UserCard.user),
                )
            ).all()
        )

        affected_users: dict[int, Counter[str]] = defaultdict(Counter)
        affected_rows: dict[str, set[str]] = defaultdict(set)
        active_benefit_ids: set[int] = set()

        for user_card in user_cards:
            for benefit in user_card.card.benefits:
                active_benefit_ids.add(benefit.id)
                reasons: list[str] = []
                if (benefit.category or "").strip() == "유의사항":
                    reasons.append("notice_row")
                if benefit.benefit_value == 0:
                    reasons.append("zero_value")
                if benefit.benefit_value is not None and not benefit.benefit_unit:
                    reasons.append("value_without_unit")
                if benefit.benefit_unit and benefit.benefit_value is None:
                    reasons.append("unit_without_value")
                if benefit.required_spending is None:
                    reasons.append("unknown_spending")
                    source_text = " ".join(
                        value or ""
                        for value in (
                            benefit.condition_text,
                            benefit.source_summary,
                            benefit.source_detail,
                        )
                    )
                    if SPENDING_CONDITION_PATTERN.search(source_text):
                        reasons.append("unstructured_spending_condition")
                if (
                    benefit.monthly_benefit_limit is None
                    and benefit.per_transaction_limit is None
                    and benefit.annual_limit is None
                    and benefit.limit_status is None
                ):
                    reasons.append("unknown_limit")

                for reason in reasons:
                    affected_users[user_card.user_id][reason] += 1
                    affected_rows[reason].add(str(benefit.source_benefit_id or benefit.id))

        all_benefits = list(db.scalars(select(CardBenefit)).all())
        global_counts = Counter()
        for benefit in all_benefits:
            if (benefit.category or "").strip() == "유의사항":
                global_counts["notice_row"] += 1
            if benefit.benefit_value == 0:
                global_counts["zero_value"] += 1
            if benefit.benefit_value is not None and not benefit.benefit_unit:
                global_counts["value_without_unit"] += 1
            if benefit.benefit_unit and benefit.benefit_value is None:
                global_counts["unit_without_value"] += 1

        print(f"active_user_cards={len(user_cards)}")
        print(f"active_card_benefits={len(active_benefit_ids)}")
        print(f"all_card_benefits={len(all_benefits)}")
        print("global_structural_risks=" + repr(dict(global_counts)))
        print("active_structural_rows=")
        for reason in (
            "zero_value",
            "value_without_unit",
            "unit_without_value",
            "notice_row",
            "unstructured_spending_condition",
        ):
            ids = sorted(affected_rows[reason])
            print(f"  {reason}={len(ids)} {ids[:100]}")
        if affected_rows["unstructured_spending_condition"]:
            print("unstructured_spending_details=")
            risky = list(
                db.scalars(
                    select(CardBenefit).where(
                        CardBenefit.source_benefit_id.in_(
                            affected_rows["unstructured_spending_condition"]
                        )
                    )
                ).all()
            )
            for benefit in sorted(risky, key=lambda item: item.source_benefit_id or ""):
                source_text = " ".join(
                    value or ""
                    for value in (
                        benefit.condition_text,
                        benefit.source_summary,
                        benefit.source_detail,
                    )
                )
                match = SPENDING_CONDITION_PATTERN.search(source_text)
                start = max((match.start() if match else 0) - 80, 0)
                print(
                    f"  {benefit.source_benefit_id}: "
                    f"{source_text[start:start + 400]!r}"
                )
        print("per_user_counts=")
        for user_id in sorted(affected_users):
            user = db.get(User, user_id)
            label = getattr(user, "name", None) or getattr(user, "email", None) or ""
            print(f"  user={user_id} label={label!r} {dict(affected_users[user_id])}")


if __name__ == "__main__":
    main()
