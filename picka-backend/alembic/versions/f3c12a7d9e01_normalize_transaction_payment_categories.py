"""normalize transaction payment categories

Revision ID: f3c12a7d9e01
Revises: e61fb9204c7d
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "f3c12a7d9e01"
down_revision: str | None = "e61fb9204c7d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


CATEGORY_NORMALIZATION = {
    "ACADEMY": "교육/육아",
    "AUTO": "자동차/정비",
    "BABY": "교육/육아",
    "BEAUTY": "뷰티/피트니스",
    "BOOKS": "교육/육아",
    "CAFE": "카페/디저트",
    "CHILD_CLASS": "교육/육아",
    "CONVENIENCE": "편의점",
    "DELIVERY": "배달앱",
    "DINING": "푸드/외식",
    "EASY_PAY": "간편결제",
    "FITNESS": "뷰티/피트니스",
    "FUEL": "주유",
    "FURNITURE": "생활",
    "GAS": "주유",
    "GROCERY": "마트/쇼핑",
    "HOUSEHOLD": "생활",
    "INSURANCE": "보험",
    "LIVING": "생활",
    "LODGING": "여행/숙박",
    "MANAGEMENT_FEE": "공과금/생활요금",
    "MART": "마트/쇼핑",
    "MEDICAL": "병원/약국",
    "MOVIE": "영화/문화",
    "ONLINE_COURSE": "교육/육아",
    "ONLINE_GROCERY": "마트/쇼핑",
    "ONLINE_SHOPPING": "온라인쇼핑",
    "PARKING": "교통",
    "PHARMACY": "병원/약국",
    "RENTAL_CAR": "자동차/정비",
    "RESTAURANT": "푸드/외식",
    "SHOPPING": "마트/쇼핑",
    "STATIONERY": "문구",
    "SUBSCRIPTION": "구독/멤버십",
    "TAXI": "교통",
    "TELECOM": "통신",
    "TOLL": "교통",
    "TRANSIT": "교통",
    "TRANSPORT": "교통",
    "TRAVEL": "여행/숙박",
    "TRAVEL_LODGING": "여행/숙박",
    "TRAVEL_SPEND": "여행/숙박",
    "TRAVEL_TRANSIT": "여행/숙박",
    "TRAVEL_TRANSPORT": "여행/숙박",
    "TUITION": "교육/육아",
}


def upgrade() -> None:
    transactions = sa.table(
        "transactions",
        sa.column("payment_category", sa.String()),
    )
    for source, target in CATEGORY_NORMALIZATION.items():
        op.execute(
            transactions.update()
            .where(transactions.c.payment_category == source)
            .values(payment_category=target)
        )


def downgrade() -> None:
    # 여러 원본 코드가 하나의 표준 카테고리로 합쳐지므로 안전한 역변환은 불가능합니다.
    pass
