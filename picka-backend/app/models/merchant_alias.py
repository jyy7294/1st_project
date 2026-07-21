from sqlalchemy import Integer, String

from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class MerchantAlias(Base):
    __tablename__ = "merchant_aliases"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    alias: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
    )

    canonical_merchant: Mapped[str] = mapped_column(
        String(255),
    )

    category: Mapped[str] = mapped_column(
        String(100),
    )

    match_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    priority: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    source: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )