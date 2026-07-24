from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, event, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserPersonaProfile(Base):
    __tablename__ = "user_persona_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    persona_id: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True, index=True
    )
    age_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    birth_date_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone_number_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    gender_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    job_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    residence_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_foreigner_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    residence_sido_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    residence_sigungu_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    child_count_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    children_age_reference_date_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    memberships_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    children_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    monthly_budget: Mapped[int | None] = mapped_column(Integer, nullable=True)
    period: Mapped[str | None] = mapped_column(String(30), nullable=True)
    preferred_benefits: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_payload_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    source_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["User"] = relationship(back_populates="persona_profile")

    def _get_text(self, field: str) -> str | None:
        pending_name = f"_pending_{field}"
        if hasattr(self, pending_name):
            return getattr(self, pending_name)
        from app.services.pii_encryption_service import decrypt_text

        return decrypt_text(
            getattr(self, f"{field}_encrypted", None),
            context=f"profile:{self.user_id}:{field}",
        )

    def _set_text(self, field: str, value: str | None) -> None:
        setattr(self, f"_pending_{field}", value)

    def _get_json(self, field: str, default: Any) -> Any:
        pending_name = f"_pending_{field}"
        if hasattr(self, pending_name):
            return getattr(self, pending_name)
        from app.services.pii_encryption_service import decrypt_json

        encrypted = getattr(self, f"{field}_encrypted", None)
        return default if encrypted is None else decrypt_json(
            encrypted,
            context=f"profile:{self.user_id}:{field}",
        )

    birth_date = property(
        lambda self: date.fromisoformat(value) if (value := self._get_text("birth_date")) else None,
        lambda self, value: self._set_text(
            "birth_date", value.isoformat() if isinstance(value, date) else value,
        ),
    )
    phone_number = property(
        lambda self: self._get_text("phone_number"),
        lambda self, value: self._set_text("phone_number", value),
    )
    residence = property(
        lambda self: self._get_text("residence"),
        lambda self, value: self._set_text("residence", value),
    )
    residence_sido = property(
        lambda self: self._get_text("residence_sido"),
        lambda self, value: self._set_text("residence_sido", value),
    )
    residence_sigungu = property(
        lambda self: self._get_text("residence_sigungu"),
        lambda self, value: self._set_text("residence_sigungu", value),
    )
    children_age_reference_date = property(
        lambda self: date.fromisoformat(value) if (
            value := self._get_text("children_age_reference_date")
        ) else None,
        lambda self, value: self._set_text(
            "children_age_reference_date",
            value.isoformat() if isinstance(value, date) else value,
        ),
    )
    memberships = property(
        lambda self: self._get_json("memberships", []),
        lambda self, value: setattr(self, "_pending_memberships", value),
    )
    children = property(
        lambda self: self._get_json("children", []),
        lambda self, value: setattr(self, "_pending_children", value),
    )
    source_payload = property(
        lambda self: self._get_json("source_payload", {}),
        lambda self, value: setattr(self, "_pending_source_payload", value),
    )
    age = property(
        lambda self: int(self._get_text("age") or 0),
        lambda self, value: self._set_text("age", str(value)),
    )
    gender = property(
        lambda self: self._get_text("gender"),
        lambda self, value: self._set_text("gender", value),
    )
    job = property(
        lambda self: self._get_text("job"),
        lambda self, value: self._set_text("job", value),
    )
    is_foreigner = property(
        lambda self: self._get_text("is_foreigner") == "true",
        lambda self, value: self._set_text(
            "is_foreigner", str(bool(value)).lower(),
        ),
    )
    child_count = property(
        lambda self: int(self._get_text("child_count") or 0),
        lambda self, value: self._set_text("child_count", str(value)),
    )


@event.listens_for(UserPersonaProfile, "before_insert")
@event.listens_for(UserPersonaProfile, "before_update")
def encrypt_profile_pii_before_write(mapper, connection, target) -> None:
    from app.services.pii_encryption_service import encrypt_json, encrypt_text

    scalar_values = {
        "age": str(target.age),
        "birth_date": target.birth_date.isoformat() if target.birth_date else None,
        "phone_number": target.phone_number,
        "gender": target.gender,
        "job": target.job,
        "residence": target.residence,
        "residence_sido": target.residence_sido,
        "residence_sigungu": target.residence_sigungu,
        "is_foreigner": str(target.is_foreigner).lower(),
        "child_count": str(target.child_count),
        "children_age_reference_date": (
            target.children_age_reference_date.isoformat()
            if target.children_age_reference_date
            else None
        ),
    }
    for field, value in scalar_values.items():
        setattr(
            target,
            f"{field}_encrypted",
            encrypt_text(value, context=f"profile:{target.user_id}:{field}"),
        )
    target.memberships_encrypted = encrypt_json(
        target.memberships,
        context=f"profile:{target.user_id}:memberships",
    )
    target.children_encrypted = encrypt_json(
        target.children,
        context=f"profile:{target.user_id}:children",
    )
    target.source_payload_encrypted = encrypt_json(
        target.source_payload,
        context=f"profile:{target.user_id}:source_payload",
    )
    for field in (
        "birth_date",
        "age",
        "phone_number",
        "gender",
        "job",
        "residence",
        "residence_sido",
        "residence_sigungu",
        "is_foreigner",
        "child_count",
        "children_age_reference_date",
        "memberships",
        "children",
        "source_payload",
    ):
        if hasattr(target, f"_pending_{field}"):
            delattr(target, f"_pending_{field}")
