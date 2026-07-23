from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CardEligibilityRule(Base):
    __tablename__ = "card_eligibility_rules"
    __table_args__ = (
        UniqueConstraint(
            "card_id",
            "eligibility_type",
            name="uq_card_eligibility_rules_card_type",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    card_id: Mapped[int] = mapped_column(
        ForeignKey("cards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    eligibility_type: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )
    comparison_operator: Mapped[str] = mapped_column(
        String(10), nullable=False, default="EQ", server_default="EQ"
    )
    required_value: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    card: Mapped["Card"] = relationship(back_populates="eligibility_rules")
