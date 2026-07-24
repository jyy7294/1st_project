from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import User, UserEligibility


SEED_PATH = (
    Path(__file__).resolve().parent.parent
    / "PICKA_supabase_core_seed_v8_7_age_updated.json"
)

PERSONA_USER_IDS = {
    "persona1": 1,
    "persona2": 2,
    "persona3": 3,
    "persona4": 4,
}

ATTRIBUTE_MAPPING = {
    "age_group": "AGE_GROUP",
    "is_student": "STUDENT",
    "military_service_target": "MILITARY_SERVICE",
    "is_business_owner": "BUSINESS_OWNER",
    "owns_light_car": "COMPACT_CAR_OWNER",
    "pregnancy_childcare_support_eligible": (
        "PREGNANCY_CHILDCARE_SUPPORT_ELIGIBLE"
    ),
    "welfare_benefit_eligible": "WELFARE_BENEFIT_ELIGIBLE",
    "occupation_qualifications": "OCCUPATION_QUALIFICATIONS",
    "telecom_provider": "TELECOM_PROVIDER",
    "primary_transport": "PRIMARY_TRANSPORT",
    "kpass_user": "KPASS_USER",
    "highpass_user": "HIGHPASS_USER",
    "preferred_airline": "PREFERRED_AIRLINE",
    "primary_shopping_affiliation": "PRIMARY_SHOPPING_AFFILIATION",
    "vehicle_owner": "VEHICLE_OWNER",
    "child_age_groups": "CHILD_AGE_GROUPS",
    "detailed_age_band": "DETAILED_AGE_BAND",
}

# Confirmed persona facts that supersede unknown values in the source seed.
CONFIRMED_OVERRIDES = {
    "persona2": {
        "MILITARY_SERVICE": ("false", "SELF_REPORTED"),
    },
    "persona3": {
        "MILITARY_SERVICE": ("false", "SELF_REPORTED"),
    },
}


def _serialize(value: object) -> str:
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False)
    return str(value).lower() if isinstance(value, bool) else str(value)


def main() -> None:
    data = json.loads(SEED_PATH.read_text(encoding="utf-8-sig"))
    tables = data["tables"]
    profiles = {row["persona_id"]: row for row in tables["profiles"]}
    persona_rows = {
        row["persona_id"]: row for row in tables["persona_eligibility"]
    }
    now = datetime.now(timezone.utc)
    inserted = 0
    updated = 0

    with SessionLocal() as db:
        existing_user_ids = set(
            db.scalars(
                select(User.id).where(User.id.in_(PERSONA_USER_IDS.values()))
            ).all()
        )
        missing = sorted(set(PERSONA_USER_IDS.values()) - existing_user_ids)
        if missing:
            raise RuntimeError(f"DB에 없는 사용자 ID: {missing}")

        for persona_id, user_id in PERSONA_USER_IDS.items():
            source = persona_rows[persona_id]
            values = {
                "AGE": str(profiles[persona_id]["age"]),
                **{
                    target: _serialize(source.get(source_key, "unknown"))
                    for source_key, target in ATTRIBUTE_MAPPING.items()
                },
            }
            overrides = CONFIRMED_OVERRIDES.get(persona_id, {})
            values.update({key: value for key, (value, _) in overrides.items()})
            for eligibility_type, value in values.items():
                override = overrides.get(eligibility_type)
                status = override[1] if override else (
                    "UNVERIFIED"
                    if value.strip().lower() in {"unknown", "[]"}
                    else "INFERRED"
                )
                eligibility = db.scalar(
                    select(UserEligibility).where(
                        UserEligibility.user_id == user_id,
                        UserEligibility.eligibility_type == eligibility_type,
                    )
                )
                if eligibility is None:
                    eligibility = UserEligibility(
                        user_id=user_id,
                        eligibility_type=eligibility_type,
                        eligibility_value=value,
                        verification_status=status,
                    )
                    db.add(eligibility)
                    inserted += 1
                else:
                    eligibility.eligibility_value = value
                    eligibility.verification_status = status
                    updated += 1
                eligibility.verified_at = None if status == "UNVERIFIED" else now
                eligibility.expires_at = None

        db.commit()

    print(f"inserted={inserted}")
    print(f"updated={updated}")


if __name__ == "__main__":
    main()
