from datetime import datetime, timedelta, timezone

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models import PrivacyAuditLog


PRIVACY_AUDIT_RETENTION_DAYS = 90


def delete_expired_privacy_audits(
    db: Session,
    *,
    now: datetime | None = None,
) -> int:
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(
        days=PRIVACY_AUDIT_RETENTION_DAYS
    )
    result = db.execute(
        delete(PrivacyAuditLog).where(PrivacyAuditLog.created_at < cutoff)
    )
    return int(result.rowcount or 0)


def save_privacy_change_audit(
    db: Session,
    *,
    actor_user_id: int,
    target_user_id: int,
    changed_fields: list[str],
) -> PrivacyAuditLog | None:
    if not changed_fields:
        return None
    audit = PrivacyAuditLog(
        actor_user_id=actor_user_id,
        target_user_id=target_user_id,
        action="PROFILE_UPDATED",
        changed_fields=sorted(set(changed_fields)),
    )
    db.add(audit)
    return audit
