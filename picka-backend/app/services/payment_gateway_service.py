from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from fastapi import HTTPException

from app.models import UserCard


@dataclass(frozen=True)
class DemoAuthorization:
    approval_number: str


def authorize_demo_payment(
    user_card: UserCard,
    *,
    payment_amount: int,
) -> DemoAuthorization:
    """Simulate the internal PG authorization boundary.

    The API receives a user-card identifier, never a payment token. The token
    remains server-side and represents the future Card Vault lookup key.
    """
    if not user_card.is_active:
        raise HTTPException(status_code=409, detail="비활성 카드입니다.")
    if not user_card.payment_token:
        raise HTTPException(
            status_code=409,
            detail="결제 토큰이 발급되지 않은 카드입니다.",
        )
    if payment_amount <= 0:
        raise HTTPException(status_code=400, detail="결제 금액이 올바르지 않습니다.")
    return DemoAuthorization(
        approval_number=f"PICKA-{uuid4().hex[:12].upper()}"
    )
