from __future__ import annotations

from typing import Any

from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TransactionBenefitOutcome(Base):
    __tablename__ = "transaction_benefit_outcomes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    recommended_card_id: Mapped[int | None] = mapped_column(
        ForeignKey("cards.id", ondelete="SET NULL"), nullable=True, index=True
    )
    card_benefit_id: Mapped[int | None] = mapped_column(
        ForeignKey("card_benefits.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    benefit_scenario: Mapped[str] = mapped_column(String(50), nullable=False)
    picka_usage_stage: Mapped[str] = mapped_column(String(50), nullable=False)
    actual_benefit_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    potential_benefit_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    missed_benefit_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    missed_benefit_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    benefit_rate_text: Mapped[str | None] = mapped_column(String(50), nullable=True)
    monthly_benefit_cap: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cap_remaining_before: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cap_remaining_after: Mapped[int | None] = mapped_column(Integer, nullable=True)
    judgement_source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reward_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    reward_program: Mapped[str | None] = mapped_column(Text, nullable=True)
    reward_amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reward_unit: Mapped[str | None] = mapped_column(String(20), nullable=True)
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    transaction: Mapped["Transaction"] = relationship(
        back_populates="benefit_outcome"
    )
