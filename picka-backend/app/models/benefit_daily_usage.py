from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class BenefitDailyUsage(Base):
    __tablename__ = "benefit_daily_usage"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "card_benefit_id",
            "usage_date",
            name="uq_benefit_daily_usage_user_benefit_date",
        ),
        CheckConstraint(
            "daily_used_amount >= 0",
            name="ck_benefit_daily_usage_amount_nonnegative",
        ),
        CheckConstraint(
            "daily_used_count >= 0",
            name="ck_benefit_daily_usage_count_nonnegative",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    card_id: Mapped[int] = mapped_column(
        ForeignKey("cards.id", ondelete="CASCADE"), nullable=False, index=True
    )
    card_benefit_id: Mapped[int] = mapped_column(
        ForeignKey("card_benefits.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    usage_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    daily_used_amount: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    daily_used_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    card_benefit: Mapped["CardBenefit"] = relationship(
        back_populates="daily_usage_records"
    )
