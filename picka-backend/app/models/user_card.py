from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserCard(Base):
    __tablename__ = "user_cards"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "card_id",
            name="uq_user_cards_user_card",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    card_id: Mapped[int] = mapped_column(
        ForeignKey("cards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nickname: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )
    selected_option_group: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )
    selected_option_benefit_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    virtual_credential_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "virtual_card_credentials.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )
    card_number_last4: Mapped[str | None] = mapped_column(
        String(4),
        nullable=True,
    )
    registration_method: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    registered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship(
        back_populates="user_cards",
    )
    card: Mapped["Card"] = relationship(
        back_populates="user_cards",
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="user_card",
        cascade="all, delete-orphan",
    )
    virtual_credential: Mapped["VirtualCardCredential | None"] = relationship(
        back_populates="user_cards"
    )
