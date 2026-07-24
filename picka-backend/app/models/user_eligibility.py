from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, event
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
    eligibility_value_encrypted: Mapped[str] = mapped_column(
        Text,
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

    @property
    def eligibility_value(self) -> str:
        pending = getattr(self, "_pending_eligibility_value", None)
        if pending is not None:
            return pending
        from app.services.pii_encryption_service import decrypt_text

        return decrypt_text(
            self.eligibility_value_encrypted,
            context=f"eligibility:{self.user_id}:{self.eligibility_type}",
        )

    @eligibility_value.setter
    def eligibility_value(self, value: str) -> None:
        self._pending_eligibility_value = value


@event.listens_for(UserEligibility, "before_insert")
@event.listens_for(UserEligibility, "before_update")
def encrypt_eligibility_value_before_write(mapper, connection, target) -> None:
    from app.services.pii_encryption_service import encrypt_text

    target.eligibility_value_encrypted = encrypt_text(
        target.eligibility_value,
        context=(
            f"eligibility:{target.user_id}:"
            f"{target.eligibility_type}"
        ),
    )
    target._pending_eligibility_value = None
