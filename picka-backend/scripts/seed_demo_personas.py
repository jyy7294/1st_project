from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import delete, func, select, text

from app.core.database import SessionLocal
from app.models import (
    BenefitUsage,
    Card,
    CardBenefit,
    MonthlyCardUsage,
    Transaction,
    User,
    UserCard,
)
from app.services.auth_service import hash_password


DATA_PATH = (
    Path(__file__).resolve().parents[1]
    / "PICKA_supabase_seed_v6_with_history.json"
)
USER_IDS = {
    "persona1": 1,
    "persona2": 3,
    "persona3": 4,
    "persona4": 5,
}
KST = timezone(timedelta(hours=9))


def load_data() -> dict:
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if "tables" not in data:
        return data

    tables = data["tables"]
    cards_by_persona: dict[str, list[dict]] = {}
    monthly_by_user_card = {
        row["user_card_id"]: row for row in tables["monthly_card_usage"]
    }
    usage_by_user_card: dict[str, list[dict]] = {}
    for row in tables["benefit_usage"]:
        usage_by_user_card.setdefault(row["user_card_id"], []).append(row)

    for row in tables["user_cards"]:
        card = dict(row)
        card["monthly_usage"] = monthly_by_user_card[row["user_card_id"]]
        card["benefit_usage"] = usage_by_user_card.get(row["user_card_id"], [])
        cards_by_persona.setdefault(row["persona_id"], []).append(card)

    transactions_by_persona: dict[str, list[dict]] = {}
    for row in tables["transactions"]:
        transactions_by_persona.setdefault(row["persona_id"], []).append(row)

    logs_by_persona: dict[str, list[dict]] = {}
    for row in tables["recommendation_logs"]:
        logs_by_persona.setdefault(row["persona_id"], []).append(row)

    return {
        "demo_accounts": [
            {
                "persona_id": profile["persona_id"],
                "name": profile["name"],
                "login_id": profile["email"],
                "password": "picka1234",
            }
            for profile in tables["profiles"]
        ],
        "personas": [
            {
                "profile": profile,
                "user_cards": cards_by_persona.get(profile["persona_id"], []),
                "transactions": transactions_by_persona.get(
                    profile["persona_id"], []
                ),
                "recommendation_logs": logs_by_persona.get(
                    profile["persona_id"], []
                ),
            }
            for profile in tables["profiles"]
        ],
    }


def seed(apply: bool) -> dict[str, int]:
    data = load_data()
    accounts = {item["persona_id"]: item for item in data["demo_accounts"]}
    personas = {
        item["profile"]["persona_id"]: item for item in data["personas"]
    }
    if set(accounts) != set(USER_IDS) or set(personas) != set(USER_IDS):
        raise RuntimeError("JSON의 페르소나 구성이 persona1~persona4와 다릅니다.")

    source_card_ids = {
        card["card_id"]
        for persona in personas.values()
        for card in persona["user_cards"]
    }
    source_benefit_ids = {
        usage["benefit_id"]
        for persona in personas.values()
        for card in persona["user_cards"]
        for usage in card.get("benefit_usage", [])
    }

    counts = {
        "users": 0,
        "user_cards": 0,
        "monthly_card_usage": 0,
        "benefit_usage": 0,
        "transactions": 0,
        "skipped_non_card_transactions": 0,
    }

    with SessionLocal() as db:
        cards = db.scalars(
            select(Card).where(Card.source_card_id.in_(source_card_ids))
        ).all()
        card_by_source = {card.source_card_id: card for card in cards}
        missing_cards = sorted(source_card_ids - set(card_by_source))
        if missing_cards:
            raise RuntimeError(f"DB에 없는 source_card_id: {missing_cards}")

        benefits = db.scalars(
            select(CardBenefit).where(
                CardBenefit.source_benefit_id.in_(source_benefit_ids)
            )
        ).all()
        benefit_by_source = {
            benefit.source_benefit_id: benefit for benefit in benefits
        }
        missing_benefits = sorted(source_benefit_ids - set(benefit_by_source))
        if missing_benefits:
            raise RuntimeError(f"DB에 없는 source_benefit_id: {missing_benefits}")

        for persona_id, target_id in USER_IDS.items():
            account = accounts[persona_id]
            persona = personas[persona_id]
            email = account["login_id"]

            id_owner = db.get(User, target_id)
            email_owner = db.scalar(select(User).where(User.email == email))
            if id_owner is not None and id_owner.email != email:
                raise RuntimeError(
                    f"users.id={target_id}가 다른 계정({id_owner.email})에 사용 중입니다."
                )
            if email_owner is not None and email_owner.id != target_id:
                raise RuntimeError(
                    f"{email}이 다른 ID({email_owner.id})에 사용 중입니다."
                )

            user = id_owner or email_owner
            if user is None:
                user = User(id=target_id, email=email, name=account["name"])
                db.add(user)
                counts["users"] += 1
            user.email = email
            user.name = account["name"]
            user.provider = "LOCAL"
            user.password_hash = hash_password(account["password"])
            user.is_active = True
            db.flush()

            db.execute(delete(Transaction).where(Transaction.user_id == target_id))
            db.execute(delete(BenefitUsage).where(BenefitUsage.user_id == target_id))
            db.execute(
                delete(MonthlyCardUsage).where(
                    MonthlyCardUsage.user_id == target_id
                )
            )
            db.execute(delete(UserCard).where(UserCard.user_id == target_id))
            db.flush()

            user_card_by_source_id: dict[str, UserCard] = {}
            for card_data in persona["user_cards"]:
                card = card_by_source[card_data["card_id"]]
                selected_option = card_data.get("selected_option")
                user_card = UserCard(
                    user_id=target_id,
                    card_id=card.id,
                    nickname=card_data.get("usage_role"),
                    is_active=bool(card_data.get("is_active", True)),
                    selected_option_group=(
                        str(selected_option) if selected_option else None
                    ),
                    card_number_last4=card_data.get("last4"),
                    registration_method="DEMO_SEED",
                    registered_at=datetime.now(KST),
                )
                db.add(user_card)
                db.flush()
                user_card_by_source_id[card_data["user_card_id"]] = user_card
                counts["user_cards"] += 1

                monthly = card_data["monthly_usage"]
                used_amount = sum(
                    int(item.get("used_benefit_amount") or 0)
                    for item in card_data.get("benefit_usage", [])
                )
                db.add(
                    MonthlyCardUsage(
                        user_id=target_id,
                        card_id=card.id,
                        usage_month=monthly["usage_month"],
                        previous_month_spending=int(
                            monthly.get("previous_month_spend") or 0
                        ),
                        current_month_spending=int(
                            monthly.get("current_month_spend") or 0
                        ),
                        card_monthly_benefit_used=used_amount,
                    )
                )
                counts["monthly_card_usage"] += 1

                for usage in card_data.get("benefit_usage", []):
                    benefit = benefit_by_source[usage["benefit_id"]]
                    db.add(
                        BenefitUsage(
                            user_id=target_id,
                            card_id=card.id,
                            card_benefit_id=benefit.id,
                            usage_month=usage["usage_month"],
                            monthly_used_amount=int(
                                usage.get("used_benefit_amount") or 0
                            ),
                            monthly_used_count=int(usage.get("used_count") or 0),
                            daily_used_count=0,
                        )
                    )
                    counts["benefit_usage"] += 1

            logs = {
                item["transaction_id"]: item
                for item in persona.get("recommendation_logs", [])
            }
            for item in persona["transactions"]:
                source_user_card_id = item.get("user_card_id")
                source_card_id = item.get("card_id")
                if not source_user_card_id or not source_card_id:
                    counts["skipped_non_card_transactions"] += 1
                    continue

                user_card = user_card_by_source_id[source_user_card_id]
                card = card_by_source[source_card_id]
                log = logs.get(item["transaction_id"], {})
                saved_amount = int(log.get("actual_benefit_amount") or 0)
                amount = int(item["amount"])
                benefit = benefit_by_source.get(log.get("actual_benefit_id"))
                approved_at = datetime.fromisoformat(item["approved_at"])
                if approved_at.tzinfo is None:
                    approved_at = approved_at.replace(tzinfo=KST)

                db.add(
                    Transaction(
                        user_id=target_id,
                        user_card_id=user_card.id,
                        card_id=card.id,
                        merchant_name=item["merchant_name"],
                        payment_category=item.get("normalized_code"),
                        original_payment_amount=amount,
                        saved_amount=saved_amount,
                        final_approved_amount=amount - saved_amount,
                        applied_benefit_name=(
                            benefit.benefit_name if benefit else None
                        ),
                        applied_benefit_category=(
                            benefit.category if benefit else None
                        ),
                        approval_number=item["transaction_id"].upper(),
                        status="APPROVED",
                        usage_month=approved_at.strftime("%Y-%m"),
                        approved_at=approved_at,
                    )
                )
                counts["transactions"] += 1

        if apply:
            db.flush()
            max_user_id = db.scalar(select(func.max(User.id))) or 1
            db.execute(
                text(
                    "SELECT setval(pg_get_serial_sequence('users', 'id'), "
                    ":value, true)"
                ),
                {"value": max_user_id},
            )
            db.commit()
        else:
            db.rollback()

    return counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--apply",
        action="store_true",
        help="검증 후 실제 DB에 반영합니다. 생략하면 롤백합니다.",
    )
    args = parser.parse_args()
    counts = seed(apply=args.apply)
    print("적재 결과" if args.apply else "검증 결과(롤백)")
    for key, value in counts.items():
        print(f"- {key}: {value}")


if __name__ == "__main__":
    main()
