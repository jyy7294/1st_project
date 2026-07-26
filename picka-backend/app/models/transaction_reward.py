from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TransactionReward(Base):
    __tablename__ = "transaction_rewards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    card_benefit_id: Mapped[int | None] = mapped_column(
        ForeignKey("card_benefits.id", ondelete="SET NULL"), nullable=True
    )
    reward_type: Mapped[str] = mapped_column(String(20), nullable=False)
    reward_program: Mapped[str] = mapped_column(String(100), nullable=False)
    reward_amount: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    reward_unit: Mapped[str] = mapped_column(String(20), nullable=False)
