from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserEligibility(Base):
    __tablename__ = "user_eligibilities"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "eligibility_type",
            name="uq_user_eligibilities_user_type",
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
    eligibility_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    eligibility_value: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    verification_status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped["User"] = relationship(back_populates="eligibilities")
