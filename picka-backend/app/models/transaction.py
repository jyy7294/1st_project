from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint(
            "original_payment_amount > 0",
            name="ck_transactions_original_amount_positive",
        ),
        CheckConstraint(
            "saved_amount >= 0",
            name="ck_transactions_saved_amount_nonnegative",
        ),
        CheckConstraint(
            "final_approved_amount >= 0",
            name="ck_transactions_final_amount_nonnegative",
        ),
        CheckConstraint(
            "saved_amount <= original_payment_amount",
            name="ck_transactions_saved_not_over_original",
        ),
        CheckConstraint(
            "final_approved_amount = original_payment_amount - saved_amount",
            name="ck_transactions_amounts_consistent",
        ),
        Index(
            "ix_transactions_user_approved_at",
            "user_id",
            "approved_at",
        ),
        Index(
            "ix_transactions_user_card_approved_at",
            "user_id",
            "card_id",
            "approved_at",
        ),
        Index(
            "ix_transactions_user_card_record_approved_at",
            "user_card_id",
            "approved_at",
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
    )
    user_card_id: Mapped[int] = mapped_column(
        ForeignKey("user_cards.id", ondelete="CASCADE"),
        nullable=False,
    )
    card_id: Mapped[int] = mapped_column(
        ForeignKey("cards.id", ondelete="CASCADE"),
        nullable=False,
    )
    merchant_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    payment_category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    original_payment_amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    saved_amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    final_approved_amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    applied_benefit_name: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    applied_benefit_category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    approval_number: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        unique=True,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="APPROVED",
        server_default="APPROVED",
    )
    usage_month: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        index=True,
    )
    approved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    user: Mapped["User"] = relationship(back_populates="transactions")
    user_card: Mapped["UserCard"] = relationship(
        back_populates="transactions"
    )
    card: Mapped["Card"] = relationship(back_populates="transactions")
