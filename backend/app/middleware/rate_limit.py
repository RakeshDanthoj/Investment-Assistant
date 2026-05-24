"""Per-user Lens query rate limiting (P2-S13)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException, status
from psycopg.rows import dict_row

from app.db.connection import connection

_LOG = logging.getLogger(__name__)

LENS_DAILY_CAP = 10


class LensDailyRateLimitError(Exception):
    """Raised when a user exceeds the daily Lens query budget."""

    def __init__(self, *, retry_after_seconds: int) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"Lens daily query limit reached ({LENS_DAILY_CAP}/day)")


def _seconds_until_utc_midnight() -> int:
    now = datetime.now(tz=UTC)
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return max(1, int((tomorrow - now).total_seconds()))


def try_consume_lens_query_slot(
    *,
    user_id: UUID,
    max_queries_per_day: int = LENS_DAILY_CAP,
) -> bool:
    """Atomically consume one Lens query slot for the user (UTC day)."""
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT public.try_consume_lens_query_slot(%s, %s) AS ok",
            (str(user_id), max_queries_per_day),
        )
        row = cur.fetchone()
    ok = bool(row and row.get("ok"))
    _LOG.info(
        "rate_limit.lens.try_consume",
        extra={"ok": ok, "user_id": str(user_id), "cap": max_queries_per_day},
    )
    return ok


def enforce_lens_daily_limit(
    *,
    user_id: UUID,
    max_queries_per_day: int = LENS_DAILY_CAP,
) -> None:
    """Raise LensDailyRateLimitError when the user is at the daily cap."""
    if try_consume_lens_query_slot(user_id=user_id, max_queries_per_day=max_queries_per_day):
        return
    raise LensDailyRateLimitError(retry_after_seconds=_seconds_until_utc_midnight())


def lens_rate_limit_http_exception(exc: LensDailyRateLimitError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "code": "lens_daily_rate_limit",
            "message": str(exc),
        },
        headers={"Retry-After": str(exc.retry_after_seconds)},
    )


__all__ = [
    "LENS_DAILY_CAP",
    "LensDailyRateLimitError",
    "enforce_lens_daily_limit",
    "lens_rate_limit_http_exception",
    "try_consume_lens_query_slot",
]
