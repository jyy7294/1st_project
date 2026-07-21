from typing import Any

from sqlalchemy import Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CardBenefit(Base):
    __tablename__ = "card_benefits"

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

    source_benefit_id: Mapped[str | None] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=True,
    )

    benefit_name: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    category: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    benefit_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    benefit_unit: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    benefit_value: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    required_spending: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    minimum_payment: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    per_transaction_limit: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    monthly_spending_limit: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    monthly_benefit_limit: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    daily_count_limit: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    monthly_count_limit: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    annual_limit: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    limit_status: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    condition_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    exception_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    raw_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    source_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    source_detail: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    additional_conditions: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    card: Mapped["Card"] = relationship(
        back_populates="benefits",
    )

    tiers: Mapped[list["BenefitTier"]] = relationship(
        "BenefitTier",
        back_populates="card_benefit",
        cascade="all, delete-orphan",
    )
    usage_records: Mapped[list["BenefitUsage"]] = relationship(
        back_populates="card_benefit",
        cascade="all, delete-orphan",
    )
