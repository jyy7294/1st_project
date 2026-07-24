from __future__ import annotations

import logging
from datetime import datetime, timedelta
from threading import Event, Thread
from zoneinfo import ZoneInfo

from sqlalchemy import select, text

from app.core.database import SessionLocal
from app.models import User
from app.services.spending_pattern_recommendation_service import (
    get_daily_card_recommendations,
)
from app.services.privacy_audit_service import delete_expired_privacy_audits
from app.services.recommendation_audit_service import (
    delete_expired_recommendation_audits,
)
from app.services.auth_service import delete_stale_refresh_tokens


logger = logging.getLogger(__name__)
KOREA = ZoneInfo("Asia/Seoul")
ADVISORY_LOCK_ID = 7_240_001


def refresh_all_daily_recommendations() -> None:
    """Ensure every user has today's recommendation snapshot.

    PostgreSQL's advisory lock prevents duplicate work when multiple API workers
    start or reach midnight at the same time.
    """
    with SessionLocal() as db:
        lock_acquired = True
        is_postgres = db.bind is not None and db.bind.dialect.name == "postgresql"
        if is_postgres:
            lock_acquired = bool(
                db.scalar(
                    text("SELECT pg_try_advisory_lock(:lock_id)"),
                    {"lock_id": ADVISORY_LOCK_ID},
                )
            )
        if not lock_acquired:
            return

        try:
            deleted_privacy_logs = delete_expired_privacy_audits(db)
            deleted_recommendation_logs = delete_expired_recommendation_audits(db)
            deleted_refresh_tokens = delete_stale_refresh_tokens(db)
            db.commit()
            user_ids = db.scalars(select(User.id).order_by(User.id)).all()
            for user_id in user_ids:
                # One invocation creates both credit and check snapshots. With
                # force_refresh=False this is idempotent for the current KST day.
                get_daily_card_recommendations(
                    db,
                    user_id=user_id,
                    card_type="credit",
                    limit=3,
                    force_refresh=False,
                )
            logger.info("Daily card recommendations ready for %d users", len(user_ids))
            logger.info(
                "Expired audit logs deleted: privacy=%d recommendation=%d",
                deleted_privacy_logs,
                deleted_recommendation_logs,
            )
            logger.info(
                "Expired or stale revoked refresh tokens deleted: %d",
                deleted_refresh_tokens,
            )
        except Exception:
            logger.exception("Failed to refresh daily card recommendations")
        finally:
            if is_postgres:
                db.execute(
                    text("SELECT pg_advisory_unlock(:lock_id)"),
                    {"lock_id": ADVISORY_LOCK_ID},
                )


class DailyRecommendationScheduler:
    def __init__(self) -> None:
        self._stop_event = Event()
        self._thread: Thread | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = Thread(
            target=self._run,
            name="daily-card-recommendation-scheduler",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2)

    def _run(self) -> None:
        # Backfill immediately after a restart, then run at every KST midnight.
        refresh_all_daily_recommendations()
        while not self._stop_event.is_set():
            now = datetime.now(KOREA)
            next_midnight = datetime.combine(
                now.date() + timedelta(days=1),
                datetime.min.time(),
                tzinfo=KOREA,
            )
            if self._stop_event.wait((next_midnight - now).total_seconds()):
                break
            refresh_all_daily_recommendations()


daily_recommendation_scheduler = DailyRecommendationScheduler()
