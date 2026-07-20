from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class VirtualCardCredential(Base):
    __tablename__ = "virtual_card_credentials"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    card_id: Mapped[int] = mapped_column(
        ForeignKey("cards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    card_number: Mapped[str] = mapped_column(
        String(19),
        nullable=False,
        unique=True,
        index=True,
    )
    expiry_month: Mapped[int] = mapped_column(Integer, nullable=False)
    expiry_year: Mapped[int] = mapped_column(Integer, nullable=False)
    cvc: Mapped[str] = mapped_column(String(3), nullable=False)
    card_password_first2: Mapped[str] = mapped_column(
        String(2),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    card: Mapped["Card"] = relationship(
        back_populates="virtual_credentials"
    )
    user_cards: Mapped[list["UserCard"]] = relationship(
        back_populates="virtual_credential"
    )
