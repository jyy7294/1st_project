from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    password_hash: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
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

    user_cards: Mapped[list["UserCard"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    monthly_card_usages: Mapped[list["MonthlyCardUsage"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    benefit_usages: Mapped[list["BenefitUsage"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    eligibilities: Mapped[list["UserEligibility"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    persona_profile: Mapped["UserPersonaProfile | None"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
