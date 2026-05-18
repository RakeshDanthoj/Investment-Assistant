"""Load recent macro/market context rows for signal corroboration (P1-S11)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from psycopg.rows import dict_row

from app.db.connection import connection
from app.services.signal_check import MarketFact


def fetch_recent_event_facts(
    *,
    since: datetime | None = None,
    reference_time: datetime | None = None,
    limit: int = 200,
) -> list[MarketFact]:
    """
    Use recently ingested editorial events as macro fact lines (title text + timestamp).

    In production this can be extended with NSE/BSE price feeds and RBI bulletins.
    """
    ref = reference_time or datetime.now(tz=UTC)
    if ref.tzinfo is None:
        ref = ref.replace(tzinfo=UTC)
    cutoff = since or (ref - timedelta(hours=6))

    stmt = """
    SELECT id::text AS source_id, title, created_at
    FROM public.events
    WHERE created_at >= %s
    ORDER BY created_at DESC
    LIMIT %s
    """
    rows: list[dict[str, Any]] = []
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, (cutoff, limit))
        rows = [dict(r) for r in cur.fetchall()]

    facts: list[MarketFact] = []
    for row in rows:
        sid = row.get("source_id") or ""
        title = str(row.get("title") or "")
        ts = row.get("created_at")
        if isinstance(ts, datetime):
            observed = ts if ts.tzinfo else ts.replace(tzinfo=UTC)
        else:
            continue
        if sid and title.strip():
            facts.append(MarketFact(source_id=sid, summary=title, observed_at=observed))
    return facts


def fact_fixture_for_tests(
    *,
    event_id: UUID | None = None,
    title: str,
    observed_at: datetime,
) -> MarketFact:
    """Build a single fact for unit/integration tests."""
    return MarketFact(
        source_id=str(event_id) if event_id else "fixture",
        summary=title,
        observed_at=observed_at,
    )
