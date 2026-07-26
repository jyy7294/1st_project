from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class BenefitUsage(Base):
    __tablename__ = "benefit_usage"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "card_benefit_id",
            "usage_month",
            name="uq_benefit_usage_user_benefit_month",
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
    card_benefit_id: Mapped[int] = mapped_column(
        ForeignKey("card_benefits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    usage_month: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        index=True,
    )
    monthly_used_amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    monthly_used_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    daily_used_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
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
        back_populates="benefit_usages",
    )
    card: Mapped["Card"] = relationship(
        back_populates="benefit_usages",
    )
    card_benefit: Mapped["CardBenefit"] = relationship(
        back_populates="usage_records",
    )
