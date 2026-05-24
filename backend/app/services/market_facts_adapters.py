"""Market-leaning fact streams for signal-monitor corroboration (P2-S14)."""

from __future__ import annotations

import hashlib
import logging
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from app.core.settings import Settings
from app.services.signal_check import MarketFact
from app.sources.base import RawEvent, SourceAdapter, SourceFailure
from app.sources.nse_announcements import NSEAnnouncementsSourceAdapter
from app.sources.nse_index import NSEIndexSnapshotAdapter

_LOG = logging.getLogger(__name__)

DEFAULT_MAX_FACTS_TOTAL = 300
DEFAULT_EVENTS_LIMIT = 200
DEFAULT_MARKET_STREAM_LIMIT = 120
MONITOR_NSE_PERIOD = "1D"
MONITOR_FETCH_WINDOW = timedelta(hours=6)


def merge_market_facts(
    *streams: Sequence[MarketFact],
    max_total: int = DEFAULT_MAX_FACTS_TOTAL,
) -> list[MarketFact]:
    """
    Merge fact streams: dedupe by ``source_id`` (keep newest ``observed_at``),
    order newest-first, cap list size.
    """
    by_id: dict[str, MarketFact] = {}
    for stream in streams:
        for fact in stream:
            existing = by_id.get(fact.source_id)
            if existing is None or fact.observed_at > existing.observed_at:
                by_id[fact.source_id] = fact

    merged = sorted(by_id.values(), key=lambda f: f.observed_at, reverse=True)
    if len(merged) > max_total:
        merged = merged[:max_total]
    return merged


def _raw_to_market_fact(
    raw: RawEvent,
    *,
    source_prefix: str,
    reference_time: datetime,
) -> MarketFact | None:
    title = (raw.title or "").strip()
    if not title:
        return None
    digest = hashlib.sha256(raw.canonical_url.encode("utf-8")).hexdigest()[:16]
    source_id = f"{source_prefix}:{digest}"
    observed = raw.published_at or reference_time
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=UTC)
    return MarketFact(source_id=source_id, summary=title, observed_at=observed)


def _adapter_facts(
    adapter: SourceAdapter,
    *,
    source_prefix: str,
    reference_time: datetime,
    window: timedelta,
    period: str | None = None,
    limit: int = DEFAULT_MARKET_STREAM_LIMIT,
) -> list[MarketFact]:
    try:
        if period is not None and isinstance(adapter, NSEAnnouncementsSourceAdapter):
            raw_rows = adapter.fetch(window, period=period)
        else:
            raw_rows = adapter.fetch(window)
    except SourceFailure as exc:
        raise exc

    facts: list[MarketFact] = []
    for raw in raw_rows:
        fact = _raw_to_market_fact(raw, source_prefix=source_prefix, reference_time=reference_time)
        if fact is not None:
            facts.append(fact)
    facts.sort(key=lambda f: f.observed_at, reverse=True)
    return facts[:limit]


def fetch_nse_announcement_facts(
    *,
    reference_time: datetime | None = None,
    window: timedelta | None = None,
    limit: int = DEFAULT_MARKET_STREAM_LIMIT,
) -> list[MarketFact]:
    ref = _ensure_utc(reference_time)
    window_eff = window or MONITOR_FETCH_WINDOW
    adapter = NSEAnnouncementsSourceAdapter()
    return _adapter_facts(
        adapter,
        source_prefix="nse",
        reference_time=ref,
        window=window_eff,
        period=MONITOR_NSE_PERIOD,
        limit=limit,
    )


def fetch_index_snapshot_facts(
    *,
    reference_time: datetime | None = None,
    window: timedelta | None = None,
    limit: int = 10,
) -> list[MarketFact]:
    ref = _ensure_utc(reference_time)
    window_eff = window or MONITOR_FETCH_WINDOW
    adapter = NSEIndexSnapshotAdapter()
    return _adapter_facts(
        adapter,
        source_prefix="nse-index",
        reference_time=ref,
        window=window_eff,
        limit=limit,
    )


def _ensure_utc(reference_time: datetime | None) -> datetime:
    ref = reference_time or datetime.now(tz=UTC)
    if ref.tzinfo is None:
        return ref.replace(tzinfo=UTC)
    return ref


def collect_market_stream_facts(
    settings: Settings,
    *,
    reference_time: datetime,
    events_facts: Sequence[MarketFact],
) -> list[Sequence[MarketFact]]:
    """Return enabled non-event streams for merge (events passed separately)."""
    streams: list[Sequence[MarketFact]] = [events_facts]
    ref = _ensure_utc(reference_time)

    if settings.signal_facts_nse_enabled:
        try:
            nse = fetch_nse_announcement_facts(reference_time=ref)
            if not nse:
                _LOG.warning(
                    "market_facts.stream_empty",
                    extra={"stream": "nse_announcements", "required": False},
                )
            else:
                _LOG.info(
                    "market_facts.stream_ok",
                    extra={"stream": "nse_announcements", "count": len(nse)},
                )
            streams.append(nse)
        except SourceFailure as exc:
            _LOG.warning(
                "market_facts.stream_error",
                extra={"stream": "nse_announcements", "error": str(exc), "required": False},
            )
    else:
        _LOG.info("market_facts.stream_disabled", extra={"stream": "nse_announcements"})

    if settings.signal_facts_index_enabled:
        try:
            index_rows = fetch_index_snapshot_facts(reference_time=ref)
            if not index_rows:
                _LOG.warning(
                    "market_facts.stream_empty",
                    extra={"stream": "nse_index", "required": False},
                )
            else:
                _LOG.info(
                    "market_facts.stream_ok",
                    extra={"stream": "nse_index", "count": len(index_rows)},
                )
            streams.append(index_rows)
        except SourceFailure as exc:
            _LOG.warning(
                "market_facts.stream_error",
                extra={"stream": "nse_index", "error": str(exc), "required": False},
            )
    else:
        _LOG.info("market_facts.stream_disabled", extra={"stream": "nse_index"})

    return streams


__all__ = [
    "DEFAULT_EVENTS_LIMIT",
    "DEFAULT_MAX_FACTS_TOTAL",
    "collect_market_stream_facts",
    "fetch_index_snapshot_facts",
    "fetch_nse_announcement_facts",
    "merge_market_facts",
]
