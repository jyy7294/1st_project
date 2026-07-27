from __future__ import annotations

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TransactionBenefitApplication(Base):
    __tablename__ = "transaction_benefit_applications"
    __table_args__ = (
        UniqueConstraint(
            "transaction_id",
            "card_benefit_id",
            name="uq_transaction_benefit_application_transaction_benefit",
        ),
        CheckConstraint(
            "applied_amount >= 0",
            name="ck_transaction_benefit_applications_amount_nonnegative",
        ),
        CheckConstraint(
            "applied_count > 0",
            name="ck_transaction_benefit_applications_count_positive",
        ),
        CheckConstraint(
            "status IN ('APPLIED', 'REVERSED')",
            name="ck_transaction_benefit_applications_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    card_benefit_id: Mapped[int | None] = mapped_column(
        ForeignKey("card_benefits.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    applied_amount: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    applied_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="APPLIED", server_default="APPLIED"
    )
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reversed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    transaction: Mapped["Transaction"] = relationship(
        back_populates="benefit_applications"
    )
    card_benefit: Mapped["CardBenefit | None"] = relationship(
        back_populates="transaction_applications"
    )
