"""Load recent macro/market context rows for signal corroboration (P1-S11, P2-S14)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from psycopg.rows import dict_row

from app.core.settings import Settings, get_settings
from app.db.connection import connection
from app.db.queries.base import SyntheticFilterMixin
from app.services.market_facts_adapters import (
    DEFAULT_EVENTS_LIMIT,
    collect_market_stream_facts,
    merge_market_facts,
)
from app.services.signal_check import MarketFact

_LOG = logging.getLogger(__name__)


def fetch_recent_event_facts(
    *,
    since: datetime | None = None,
    reference_time: datetime | None = None,
    limit: int = DEFAULT_EVENTS_LIMIT,
) -> list[MarketFact]:
    """
    Use recently ingested editorial events as macro fact lines (title text + timestamp).
    """
    ref = reference_time or datetime.now(tz=UTC)
    if ref.tzinfo is None:
        ref = ref.replace(tzinfo=UTC)
    cutoff = since or (ref - timedelta(hours=6))

    synth = SyntheticFilterMixin.events_not_synthetic("events")
    stmt = f"""
    SELECT id::text AS source_id, title, created_at
    FROM public.events
    WHERE created_at >= %s
      AND {synth}
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
            facts.append(
                MarketFact(
                    source_id=f"event:{sid}",
                    summary=title,
                    observed_at=observed,
                )
            )
    return facts


def build_market_facts(
    *,
    reference_time: datetime | None = None,
    settings: Settings | None = None,
) -> list[MarketFact]:
    """
    Production default: merge recent ``events`` rows with market-leaning streams.

    * **events** — required in production when enabled; DB-backed macro proxy.
    * **nse_announcements** / **nse_index** — optional; failures log and continue.
    """
    cfg = settings or get_settings()
    ref = reference_time or datetime.now(tz=UTC)
    if ref.tzinfo is None:
        ref = ref.replace(tzinfo=UTC)

    events_facts: list[MarketFact] = []
    if cfg.signal_facts_events_enabled:
        try:
            events_facts = fetch_recent_event_facts(reference_time=ref)
            if not events_facts:
                _LOG.warning(
                    "market_facts.stream_empty",
                    extra={"stream": "events", "required": True},
                )
            else:
                _LOG.info(
                    "market_facts.stream_ok",
                    extra={"stream": "events", "count": len(events_facts)},
                )
        except RuntimeError as exc:
            _LOG.warning(
                "market_facts.stream_error",
                extra={"stream": "events", "error": str(exc), "required": True},
            )
            raise
    else:
        _LOG.warning(
            "market_facts.stream_disabled",
            extra={"stream": "events", "note": "events_disabled_in_env"},
        )

    streams = collect_market_stream_facts(cfg, reference_time=ref, events_facts=events_facts)
    merged = merge_market_facts(*streams, max_total=cfg.signal_facts_max_total)

    if not merged and cfg.signal_facts_events_enabled:
        _LOG.warning("market_facts.merge_empty", extra={"reference_time": ref.isoformat()})

    _LOG.info(
        "market_facts.build_complete",
        extra={
            "total": len(merged),
            "events": len(events_facts),
            "streams": len(streams),
        },
    )
    return merged


def fact_fixture_for_tests(
    *,
    event_id: UUID | None = None,
    title: str,
    observed_at: datetime,
) -> MarketFact:
    """Build a single fact for unit/integration tests."""
    prefix = str(event_id) if event_id else "fixture"
    return MarketFact(
        source_id=f"event:{prefix}",
        summary=title,
        observed_at=observed_at,
    )
