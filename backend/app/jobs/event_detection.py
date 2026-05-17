"""4-hour event-ingest job wiring adapters → Supabase `events` table (P1-S6)."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from datetime import timedelta

from app.core.settings import get_settings
from app.services.event_classification import infer_event_category
from app.services.event_confidence import score
from app.services.event_persistence import persist_draft_event
from app.sources.base import AdapterSource, RawEvent, SourceAdapter, SourceFailure
from app.sources.newsapi import NewsAPISourceAdapter
from app.sources.nse_announcements import NSEAnnouncementsSourceAdapter
from app.sources.rbi_rss import RBIRSSSourceAdapter

_LOG = logging.getLogger(__name__)


@dataclass
class DetectionRunSummary:
    inserted: int = 0
    duplicates: int = 0
    errors: int = 0
    skipped_config: int = 0
    source_failures: list[str] = field(default_factory=list)


def default_adapters() -> list[SourceAdapter]:
    settings = get_settings()
    return [
        RBIRSSSourceAdapter(),
        NewsAPISourceAdapter(api_key=settings.newsapi_key),
        NSEAnnouncementsSourceAdapter(),
    ]


PersistFn = Callable[..., str]


def run_event_detection(
    *,
    adapters: Sequence[SourceAdapter] | None = None,
    window: timedelta | None = None,
    persist: PersistFn | None = None,
) -> DetectionRunSummary:
    adapters_list = list(adapters) if adapters is not None else default_adapters()
    window_eff = window or timedelta(hours=4)
    persist_fn: PersistFn = persist or persist_draft_event

    summary = DetectionRunSummary()

    for adapter in adapters_list:
        try:
            raw_rows = adapter.fetch(window_eff)
        except SourceFailure as exc:
            _LOG.warning(
                "event_detection.adapter_failed",
                extra={"source": adapter.adapter_source.value, "error": str(exc)},
            )
            summary.source_failures.append(adapter.adapter_source.value)
            continue

        adapter_source = adapter.adapter_source
        for raw in raw_rows:
            summary = _persist_single(raw, adapter_source, persist_fn, summary)

    _LOG.info(
        "event_detection.complete",
        extra={
            "inserted": summary.inserted,
            "duplicates": summary.duplicates,
            "errors": summary.errors,
            "skipped_config": summary.skipped_config,
            "source_failures": summary.source_failures,
        },
    )
    return summary


def _persist_single(
    raw: RawEvent,
    adapter_src: AdapterSource,
    persist_fn: PersistFn,
    summary: DetectionRunSummary,
) -> DetectionRunSummary:
    cat = infer_event_category(adapter_src, raw)
    score_val = score(adapter_src, raw)

    outcome = persist_fn(
        title=raw.title,
        category=cat,
        event_source=adapter_src,
        canonical_url=raw.canonical_url,
        confidence_score=score_val,
        source_url=None,
    )
    if outcome == "inserted":
        summary.inserted += 1
    elif outcome == "duplicate":
        summary.duplicates += 1
    elif outcome == "skipped_no_config":
        summary.skipped_config += 1
    else:
        summary.errors += 1
    return summary


def main(argv: Iterable[str] | None = None) -> None:
    del argv  # reserved for CLI flags later
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_event_detection()


if __name__ == "__main__":
    main()
