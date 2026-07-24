from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import User, UserPersonaProfile
from app.services.pii_encryption_service import (
    decrypt_text,
    email_blind_index,
    encrypt_text,
    normalize_email,
)


def main() -> None:
    counts = {"users": 0, "profiles": 0}
    with SessionLocal() as db:
        for user in db.scalars(select(User)).all():
            normalized = normalize_email(user.email)
            index = email_blind_index(normalized)
            user.email = normalized
            user.email_blind_index = index
            user.email_encrypted = encrypt_text(normalized, context="user:email")
            user.name_encrypted = encrypt_text(
                user.name,
                context=f"user:{index}:name",
            )
            counts["users"] += 1
        for profile in db.scalars(select(UserPersonaProfile)).all():
            values = {
                "age": str(profile.age),
                "gender": profile.gender,
                "job": profile.job,
                "is_foreigner": str(profile.is_foreigner).lower(),
                "child_count": str(profile.child_count),
            }
            for field, value in values.items():
                setattr(
                    profile,
                    f"{field}_encrypted",
                    encrypt_text(value, context=f"profile:{profile.user_id}:{field}"),
                )
            counts["profiles"] += 1
        db.commit()

        for user in db.scalars(select(User)).all():
            assert decrypt_text(user.email_encrypted, context="user:email") == user.email
            assert decrypt_text(
                user.name_encrypted,
                context=f"user:{user.email_blind_index}:name",
            ) == user.name
        for profile in db.scalars(select(UserPersonaProfile)).all():
            checks = {
                "age": str(profile.age),
                "gender": profile.gender,
                "job": profile.job,
                "is_foreigner": str(profile.is_foreigner).lower(),
                "child_count": str(profile.child_count),
            }
            for field, expected in checks.items():
                assert decrypt_text(
                    getattr(profile, f"{field}_encrypted"),
                    context=f"profile:{profile.user_id}:{field}",
                ) == expected
    print(counts)


if __name__ == "__main__":
    main()
