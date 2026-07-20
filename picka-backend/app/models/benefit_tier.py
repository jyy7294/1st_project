from typing import Any

from sqlalchemy import Boolean, Float, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class BenefitTier(Base):
    __tablename__ = "benefit_tiers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    card_benefit_id: Mapped[int] = mapped_column(
        ForeignKey(
            "card_benefits.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )
    source_benefit_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    tier_order: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    required_spending: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    monthly_limit: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    benefit_value: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    benefit_unit: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    extraction_method: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    review_required: Mapped[bool | None] = mapped_column(
        Boolean,
        nullable=True,
    )
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    card_benefit: Mapped["CardBenefit"] = relationship(
        "CardBenefit",
        back_populates="tiers",
    )
