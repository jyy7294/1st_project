from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    MonthlyCardUsage,
    User,
    UserCard,
    VirtualCardCredential,
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
) -> tuple[UserCard, VirtualCardCredential]:
    if db.get(User, user_id) is None:
        raise HTTPException(
            status_code=404,
            detail=f"사용자 ID {user_id}를 찾을 수 없습니다.",
        )

    credential = db.scalar(
        select(VirtualCardCredential).where(
            VirtualCardCredential.card_number == card_number,
            VirtualCardCredential.expiry_month == expiry_month,
            VirtualCardCredential.expiry_year == expiry_year,
            VirtualCardCredential.cvc == cvc,
            VirtualCardCredential.card_password_first2
            == card_password_first2,
        )
    )
    if credential is None:
        raise HTTPException(
            status_code=400,
            detail="입력한 카드 정보를 확인할 수 없습니다.",
        )

    user_card = db.scalar(
        select(UserCard).where(
            UserCard.user_id == user_id,
            UserCard.card_id == credential.card_id,
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
            card_id=credential.card_id,
        )
        db.add(user_card)

    user_card.virtual_credential_id = credential.id
    # PG 결제수단 식별자는 카드 등록(또는 재등록) 시 새로 발급한다.
    # 전체 카드번호, CVC, 카드 비밀번호는 이 토큰에 포함되지 않는다.
    user_card.payment_token = f"picka_pg_{uuid4().hex}"
    user_card.card_number_last4 = credential.card_number[-4:]
    user_card.registration_method = registration_method
    user_card.registered_at = now
    user_card.is_active = True

    monthly_usage = db.scalar(
        select(MonthlyCardUsage).where(
            MonthlyCardUsage.user_id == user_id,
            MonthlyCardUsage.card_id == credential.card_id,
            MonthlyCardUsage.usage_month == usage_month,
        )
    )
    if monthly_usage is None:
        db.add(
            MonthlyCardUsage(
                user_id=user_id,
                card_id=credential.card_id,
                usage_month=usage_month,
                previous_month_spending=0,
                current_month_spending=0,
                card_monthly_benefit_used=0,
            )
        )

    db.commit()
    db.refresh(user_card)
    return user_card, credential
