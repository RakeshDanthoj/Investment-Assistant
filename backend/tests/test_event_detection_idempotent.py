from __future__ import annotations

from datetime import timedelta

from app.jobs.event_detection import run_event_detection
from app.models.enums import EventCategory
from app.sources.base import AdapterSource, RawEvent, SourceAdapter


class FrozenAdapter(SourceAdapter):
    adapter_source = AdapterSource.NEWSAPI

    def __init__(self, frozen: RawEvent) -> None:
        self._frozen = frozen

    def fetch(self, window: timedelta) -> list[RawEvent]:
        del window
        return [self._frozen]


def test_second_detection_run_is_duplicate() -> None:
    sample = RawEvent(
        title="Headline dup",
        canonical_url="https://example.com/canonical-stable",
        published_at=None,
        excerpt=None,
    )
    inserted_keys: set[tuple[str, str]] = set()

    def persist_track(
        *,
        title: str,
        category: EventCategory,
        event_source: AdapterSource | str,
        canonical_url: str,
        confidence_score: int,
        source_url: str | None,
    ) -> str:
        del title, category, confidence_score, source_url
        src_val = event_source.value if isinstance(event_source, AdapterSource) else event_source
        key = (src_val, canonical_url)
        if key in inserted_keys:
            return "duplicate"
        inserted_keys.add(key)
        return "inserted"

    s1 = run_event_detection(adapters=[FrozenAdapter(sample)], persist=persist_track)
    s2 = run_event_detection(adapters=[FrozenAdapter(sample)], persist=persist_track)

    assert s1.inserted == 1 and s1.duplicates == 0
    assert s2.inserted == 0 and s2.duplicates == 1
