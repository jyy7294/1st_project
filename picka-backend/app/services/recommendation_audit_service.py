from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models import RecommendationAuditLog


AUDIT_RETENTION_DAYS = 90


def delete_expired_recommendation_audits(
    db: Session,
    *,
    now: datetime | None = None,
) -> int:
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(
        days=AUDIT_RETENTION_DAYS
    )
    result = db.execute(
        delete(RecommendationAuditLog).where(
            RecommendationAuditLog.created_at < cutoff
        )
    )
    return int(result.rowcount or 0)


def save_recommendation_audit(
    db: Session,
    *,
    user_id: int,
    request_kind: str,
    input_payload: dict[str, Any],
    calculation_payload: dict[str, Any],
    usage_month: str | None = None,
    selected_card_id: int | None = None,
    policy_version: str | None = None,
    cache_hit: bool = False,
) -> RecommendationAuditLog:
    """추천 요청 당시 입력과 전체 계산 결과를 변경 불가능한 새 행으로 남긴다."""
    delete_expired_recommendation_audits(db)
    audit = RecommendationAuditLog(
        user_id=user_id,
        request_kind=request_kind,
        usage_month=usage_month,
        selected_card_id=selected_card_id,
        input_payload=input_payload,
        calculation_payload=calculation_payload,
        policy_version=policy_version,
        cache_hit=cache_hit,
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit
