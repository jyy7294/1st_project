from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from fastapi import HTTPException


# 발표·테스트용 BIN → 카드 상품 매핑이다. 실제 운영에서는 이 파일이 아니라
# 카드사/매입사 네트워크가 카드 상품을 식별한다.
DEMO_BIN_CARD_MAP = {
    "111122": 53,
    "555566": 13,
    "999900": 78,
    "123456": 4,
}


@dataclass(frozen=True)
class VaultTokenizationResult:
    card_id: int
    payment_token: str
    card_number_last4: str
    expiry_month: int
    expiry_year: int


def tokenize_card_with_mock_vault(
    *,
    card_number: str,
    expiry_month: int,
    expiry_year: int,
    cvc: str,
    card_password_first2: str,
) -> VaultTokenizationResult:
    """Simulate the future external PCI card vault boundary.

    Sensitive inputs are accepted only for this call and are never persisted or
    returned. A real provider would validate them over a protected connection.
    """
    del cvc, card_password_first2
    card_id = DEMO_BIN_CARD_MAP.get(card_number[:6])
    if card_id is None:
        raise HTTPException(
            status_code=400,
            detail="모의 PG에서 지원하지 않는 테스트 카드입니다.",
        )
    return VaultTokenizationResult(
        card_id=card_id,
        payment_token=f"picka_pg_{uuid4().hex}",
        card_number_last4=card_number[-4:],
        expiry_month=expiry_month,
        expiry_year=expiry_year,
    )
