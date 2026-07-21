from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Card(Base):
    __tablename__ = "cards"

    # 우리 DB에서 사용하는 내부 ID
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # 카드고릴라 등 원본 데이터의 카드 식별자
    source_card_id: Mapped[int | None] = mapped_column(
        Integer,
        unique=True,
        nullable=True,
        index=True,
    )

    card_name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )

    issuer: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )

    card_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    annual_fee: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # 카드의 대표 전월 실적 조건
    previous_spending: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # 카드 전체에 적용되는 월 통합한도
    monthly_total_limit: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    image_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    source_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # 발급 가능·사용 가능 여부
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    # 전처리된 원본 데이터 보존
    raw_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
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

    benefits: Mapped[list["CardBenefit"]] = relationship(
        back_populates="card",
        cascade="all, delete-orphan",
    )
    user_cards: Mapped[list["UserCard"]] = relationship(
        back_populates="card",
        cascade="all, delete-orphan",
    )
    monthly_card_usages: Mapped[list["MonthlyCardUsage"]] = relationship(
        back_populates="card",
        cascade="all, delete-orphan",
    )
    benefit_usages: Mapped[list["BenefitUsage"]] = relationship(
        back_populates="card",
        cascade="all, delete-orphan",
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="card",
        cascade="all, delete-orphan",
    )
    virtual_credentials: Mapped[list["VirtualCardCredential"]] = relationship(
        back_populates="card",
        cascade="all, delete-orphan",
    )
