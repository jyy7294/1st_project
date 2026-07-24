from __future__ import annotations

from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    MonthlyCardUsage,
    Card,
    User,
    UserCard,
)
from app.services.mock_card_vault_service import (
    VaultTokenizationResult,
    tokenize_card_with_mock_vault,
)


def register_virtual_card(
    db: Session,
    user_id: int,
    card_number: str,
    expiry_month: int,
    expiry_year: int,
    cvc: str,
    card_password_first2: str,
    registration_method: str,
    usage_month: str,
) -> tuple[UserCard, VaultTokenizationResult]:
    if db.get(User, user_id) is None:
        raise HTTPException(
            status_code=404,
            detail=f"사용자 ID {user_id}를 찾을 수 없습니다.",
        )

    tokenization = tokenize_card_with_mock_vault(
        card_number=card_number,
        expiry_month=expiry_month,
        expiry_year=expiry_year,
        cvc=cvc,
        card_password_first2=card_password_first2,
    )
    if db.get(Card, tokenization.card_id) is None:
        raise HTTPException(
            status_code=400,
            detail="모의 PG가 식별한 카드 상품이 DB에 없습니다.",
        )

    user_card = db.scalar(
        select(UserCard).where(
            UserCard.user_id == user_id,
            UserCard.card_id == tokenization.card_id,
        )
    )
    if user_card is not None and user_card.is_active:
        raise HTTPException(
            status_code=409,
            detail="이미 등록된 카드입니다.",
        )

    now = datetime.now(timezone.utc)
    if user_card is None:
        user_card = UserCard(
            user_id=user_id,
            card_id=tokenization.card_id,
        )
        db.add(user_card)

    user_card.payment_token = tokenization.payment_token
    user_card.card_number_last4 = tokenization.card_number_last4
    user_card.registration_method = registration_method
    user_card.registered_at = now
    user_card.is_active = True

    monthly_usage = db.scalar(
        select(MonthlyCardUsage).where(
            MonthlyCardUsage.user_id == user_id,
            MonthlyCardUsage.card_id == tokenization.card_id,
            MonthlyCardUsage.usage_month == usage_month,
        )
    )
    if monthly_usage is None:
        db.add(
            MonthlyCardUsage(
                user_id=user_id,
                card_id=tokenization.card_id,
                usage_month=usage_month,
                previous_month_spending=0,
                current_month_spending=0,
                card_monthly_benefit_used=0,
            )
        )

    db.commit()
    db.refresh(user_card)
    return user_card, tokenization
