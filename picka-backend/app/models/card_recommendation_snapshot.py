from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CardRecommendationSnapshot(Base):
    __tablename__ = "card_recommendation_snapshots"
    __table_args__ = (
        UniqueConstraint("user_id", "analysis_date", name="uq_card_recommendation_snapshot_user_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    analysis_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    credit_result: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    check_result: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    policy_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="legacy",
    )
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
