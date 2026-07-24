from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, Text, event, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('USER', 'ADMIN')",
            name="ck_users_role",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    email_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    email_blind_index: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True,
    )
    name_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
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
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="USER",
        server_default="USER",
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
    refresh_tokens: Mapped[list["AuthRefreshToken"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    @property
    def email(self) -> str:
        pending = getattr(self, "_pending_email", None)
        if pending is not None:
            return pending
        from app.services.pii_encryption_service import decrypt_text

        return decrypt_text(self.email_encrypted, context="user:email")

    @email.setter
    def email(self, value: str) -> None:
        self._pending_email = value

    @property
    def name(self) -> str:
        pending = getattr(self, "_pending_name", None)
        if pending is not None:
            return pending
        from app.services.pii_encryption_service import decrypt_text

        return decrypt_text(
            self.name_encrypted,
            context=f"user:{self.email_blind_index}:name",
        )

    @name.setter
    def name(self, value: str) -> None:
        self._pending_name = value


@event.listens_for(User, "before_insert")
@event.listens_for(User, "before_update")
def encrypt_user_identity_before_write(mapper, connection, target) -> None:
    from app.services.pii_encryption_service import (
        email_blind_index,
        encrypt_text,
        normalize_email,
    )

    normalized_email = normalize_email(target.email)
    target.email_blind_index = email_blind_index(normalized_email)
    target.email_encrypted = encrypt_text(
        normalized_email,
        context="user:email",
    )
    target.name_encrypted = encrypt_text(
        target.name,
        context=f"user:{target.email_blind_index}:name",
    )
    target._pending_email = None
    target._pending_name = None
