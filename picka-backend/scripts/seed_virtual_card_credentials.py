from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Card, VirtualCardCredential


VIRTUAL_CARDS = (
    {
        "card_id": 53,
        "card_number": "1111222233334444",
        "expiry_month": 12,
        "expiry_year": 2029,
        "cvc": "123",
        "card_password_first2": "45",
    },
    {
        "card_id": 13,
        "card_number": "5555666677778888",
        "expiry_month": 6,
        "expiry_year": 2030,
        "cvc": "456",
        "card_password_first2": "78",
    },
    {
        "card_id": 78,
        "card_number": "9999000011112222",
        "expiry_month": 9,
        "expiry_year": 2028,
        "cvc": "789",
        "card_password_first2": "12",
    },
)


def main() -> None:
    created = 0
    with SessionLocal() as db:
        for data in VIRTUAL_CARDS:
            if db.get(Card, data["card_id"]) is None:
                raise RuntimeError(
                    f"카드 ID {data['card_id']}가 DB에 없습니다."
                )
            credential = db.scalar(
                select(VirtualCardCredential).where(
                    VirtualCardCredential.card_number
                    == data["card_number"]
                )
            )
            if credential is None:
                credential = VirtualCardCredential()
                db.add(credential)
                created += 1
            for field, value in data.items():
                setattr(credential, field, value)
        db.commit()
    print(f"가상 카드 인증정보 Seed 완료: 생성 {created}건")


if __name__ == "__main__":
    main()
