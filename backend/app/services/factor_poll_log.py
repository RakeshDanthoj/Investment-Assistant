"""Audit log for NewsAPI factor polls (P3-S1d)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from psycopg.rows import dict_row

from app.db.connection import connection

_LOG = logging.getLogger(__name__)

PollStatus = str  # ok | empty | error

INSERT_POLL_SQL = """
INSERT INTO public.factor_poll_log (factor_id, polled_at, status, article_count)
VALUES (%s, COALESCE(%s, now()), %s, %s)
RETURNING id
"""

LAST_POLLED_SLUG_SQL = """
SELECT f.slug
FROM public.factor_poll_log p
JOIN public.factors f ON f.id = p.factor_id
ORDER BY p.polled_at DESC
LIMIT 1
"""

COUNTS_TODAY_SQL = """
SELECT f.slug, COUNT(*)::int AS poll_count
FROM public.factor_poll_log p
JOIN public.factors f ON f.id = p.factor_id
WHERE p.polled_at >= (timezone('utc', now()))::date
GROUP BY f.slug
"""

FACTOR_ID_BY_SLUG_SQL = "SELECT id FROM public.factors WHERE slug = %s"

RECENT_POLLS_SQL = """
SELECT
  f.slug,
  f.display_name,
  p.polled_at,
  p.status,
  p.article_count
FROM public.factor_poll_log p
JOIN public.factors f ON f.id = p.factor_id
ORDER BY p.polled_at DESC
LIMIT %s
"""


@dataclass(frozen=True)
class FactorPollRow:
    slug: str
    display_name: str
    polled_at: datetime
    status: PollStatus
    article_count: int


def _factor_id_for_slug(cur, slug: str) -> UUID | None:
    cur.execute(FACTOR_ID_BY_SLUG_SQL, (slug,))
    row = cur.fetchone()
    if row is None:
        return None
    return row[0] if not isinstance(row, dict) else row["id"]


def record_factor_poll(
    *,
    factor_slug: str,
    status: PollStatus,
    article_count: int,
    polled_at: datetime | None = None,
) -> UUID | None:
    """Persist one poll outcome. Returns row id, or None when factor slug is unknown."""
    try:
        with connection() as conn, conn.cursor() as cur:
            factor_id = _factor_id_for_slug(cur, factor_slug)
            if factor_id is None:
                _LOG.warning(
                    "factor_poll_log.unknown_factor",
                    extra={"factor_slug": factor_slug},
                )
                return None
            cur.execute(
                INSERT_POLL_SQL,
                (factor_id, polled_at, status, article_count),
            )
            row = cur.fetchone()
            conn.commit()
            return row[0] if row else None
    except Exception:
        _LOG.exception(
            "factor_poll_log.write_failed",
            extra={"factor_slug": factor_slug, "status": status},
        )
        return None


def last_polled_factor_slug() -> str | None:
    try:
        with connection() as conn, conn.cursor() as cur:
            cur.execute(LAST_POLLED_SLUG_SQL)
            row = cur.fetchone()
            return row[0] if row else None
    except Exception:
        _LOG.exception("factor_poll_log.last_polled_read_failed")
        return None


def factor_poll_counts_today() -> dict[str, int]:
    try:
        with connection() as conn, conn.cursor() as cur:
            cur.execute(COUNTS_TODAY_SQL)
            return {row[0]: int(row[1]) for row in cur.fetchall()}
    except Exception:
        _LOG.exception("factor_poll_log.counts_today_read_failed")
        return {}


def recent_factor_polls(*, limit: int = 8) -> list[FactorPollRow]:
    try:
        with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(RECENT_POLLS_SQL, (limit,))
            rows = cur.fetchall()
    except Exception:
        _LOG.exception("factor_poll_log.recent_read_failed")
        return []

    out: list[FactorPollRow] = []
    for row in rows:
        polled = row["polled_at"]
        if polled.tzinfo is None:
            polled = polled.replace(tzinfo=UTC)
        out.append(
            FactorPollRow(
                slug=row["slug"],
                display_name=row["display_name"],
                polled_at=polled,
                status=row["status"],
                article_count=int(row["article_count"]),
            )
        )
    return out
