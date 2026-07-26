from __future__ import annotations

from app.core.database import SessionLocal
from app.models import UserEligibility, UserPersonaProfile
from app.services.pii_encryption_service import (
    decrypt_json,
    decrypt_text,
    encrypt_json,
    encrypt_text,
)


def _encrypt_profile(profile: UserPersonaProfile) -> int:
    values = {
        "birth_date": profile.birth_date.isoformat() if profile.birth_date else None,
        "phone_number": profile.phone_number,
        "residence": profile.residence,
        "residence_sido": profile.residence_sido,
        "residence_sigungu": profile.residence_sigungu,
        "children_age_reference_date": (
            profile.children_age_reference_date.isoformat()
            if profile.children_age_reference_date
            else None
        ),
    }
    changed = 0
    for field, plaintext in values.items():
        encrypted_field = f"{field}_encrypted"
        encrypted = getattr(profile, encrypted_field)
        context = f"profile:{profile.user_id}:{field}"
        if encrypted is not None:
            if decrypt_text(encrypted, context=context) != plaintext:
                raise RuntimeError(f"암호문 대조 실패: profile={profile.id}, field={field}")
            continue
        setattr(profile, encrypted_field, encrypt_text(plaintext, context=context))
        changed += int(plaintext is not None)

    for field, plaintext in (
        ("memberships", profile.memberships),
        ("children", profile.children),
        ("source_payload", profile.source_payload),
    ):
        encrypted_field = f"{field}_encrypted"
        encrypted = getattr(profile, encrypted_field)
        context = f"profile:{profile.user_id}:{field}"
        if encrypted is not None:
            if decrypt_json(encrypted, context=context) != plaintext:
                raise RuntimeError(f"암호문 대조 실패: profile={profile.id}, field={field}")
            continue
        setattr(profile, encrypted_field, encrypt_json(plaintext, context=context))
        changed += 1
    return changed


def main() -> None:
    counts = {"profile_fields": 0, "eligibilities": 0}
    with SessionLocal() as db:
        for profile in db.query(UserPersonaProfile).yield_per(100):
            counts["profile_fields"] += _encrypt_profile(profile)
        for eligibility in db.query(UserEligibility).yield_per(500):
            context = (
                f"eligibility:{eligibility.user_id}:"
                f"{eligibility.eligibility_type}"
            )
            if eligibility.eligibility_value_encrypted is not None:
                decrypted = decrypt_text(
                    eligibility.eligibility_value_encrypted,
                    context=context,
                )
                if decrypted != eligibility.eligibility_value:
                    raise RuntimeError(
                        f"암호문 대조 실패: eligibility={eligibility.id}"
                    )
                continue
            eligibility.eligibility_value_encrypted = encrypt_text(
                eligibility.eligibility_value,
                context=context,
            )
            counts["eligibilities"] += 1
        db.commit()
    print(counts)


if __name__ == "__main__":
    main()
