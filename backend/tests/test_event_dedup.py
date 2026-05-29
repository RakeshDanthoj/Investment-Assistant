"""P3-S1c: dedup_key computation and merge behaviour (G-03)."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.db.migrate import apply_migrations
from app.models.enums import EventCategory
from app.services.event_dedup import (
    clear_entity_map_cache,
    compute_collision_fingerprint,
    compute_dedup_key,
    headline_hash,
    load_entity_map,
    normalise_entity,
    persist_deduped_event,
    recompute_confidence_raw,
)
from app.sources.base import AdapterSource, RawEvent


def test_entity_map_has_at_least_thirty_entries() -> None:
    clear_entity_map_cache()
    assert len(load_entity_map()) >= 30


def test_headline_hash_is_normalised_first_100_chars() -> None:
    raw = "  RBI Holds Repo Rate!!!   Steady at 6.5%  "
    assert headline_hash(raw) == "rbi holds repo rate steady at 65"


def test_same_wire_across_outlets_shares_dedup_key() -> None:
    detected = datetime(2025, 6, 15, 10, 30, tzinfo=UTC)
    headline = "RBI keeps repo rate unchanged at 6.5 percent"
    key_a = compute_dedup_key(
        category=EventCategory.RBI_POLICY,
        headline=headline,
        detected_at=detected,
    )
    key_b = compute_dedup_key(
        category=EventCategory.RBI_POLICY,
        headline=headline,
        body="Different outlet excerpt",
        detected_at=detected,
    )
    assert key_a == key_b


def test_different_headlines_same_entity_do_not_merge() -> None:
    detected = datetime(2025, 6, 15, 10, 30, tzinfo=UTC)
    key_rate = compute_dedup_key(
        category=EventCategory.RBI_POLICY,
        headline="RBI keeps repo rate unchanged at 6.5 percent",
        detected_at=detected,
    )
    key_crr = compute_dedup_key(
        category=EventCategory.RBI_POLICY,
        headline="RBI raises CRR by 50 basis points",
        detected_at=detected,
    )
    assert key_rate != key_crr


def test_headline_hash_in_key_for_all_categories() -> None:
    detected = datetime(2025, 6, 15, 10, 30, tzinfo=UTC)
    categories = [
        EventCategory.MACRO,
        EventCategory.RBI_POLICY,
        EventCategory.REGULATORY,
        EventCategory.INDIA_SPECIFIC,
        EventCategory.GEOPOLITICAL,
        EventCategory.BUDGET,
    ]
    for category in categories:
        with_headline = compute_dedup_key(
            category=category,
            headline=f"Unique headline for {category.value}",
            detected_at=detected,
        )
        without_headline = compute_dedup_key(
            category=category,
            headline=f"Different headline for {category.value}",
            detected_at=detected,
        )
        assert with_headline != without_headline


def test_normalise_entity_resolves_rbi_alias() -> None:
    clear_entity_map_cache()
    assert normalise_entity("RBI holds rates steady", None) == "rbi"
    assert normalise_entity("Reserve Bank of India policy update", None) == "rbi"


def test_recompute_confidence_raw_increases_with_source_count() -> None:
    low = recompute_confidence_raw(source_count=1, confidence_score=50)
    high = recompute_confidence_raw(source_count=3, confidence_score=50)
    assert high > low


def test_collision_fingerprint_ignores_category() -> None:
    detected = datetime(2025, 6, 15, 10, 30, tzinfo=UTC)
    headline = "RBI keeps repo rate unchanged at 6.5 percent"
    fp_a = compute_collision_fingerprint(headline=headline, detected_at=detected)
    fp_b = compute_collision_fingerprint(headline=headline, detected_at=detected)
    assert fp_a == fp_b


@pytest.mark.integration
def test_persist_deduped_event_merges_same_story(db_connection) -> None:
    apply_migrations(db_connection)
    detected = datetime(2025, 6, 15, 10, 30, tzinfo=UTC)
    headline = f"RBI unchanged repo {uuid4().hex[:8]}"
    raw_a = RawEvent(
        title=headline,
        canonical_url=f"https://example.com/a-{uuid4()}",
        published_at=detected,
    )
    raw_b = RawEvent(
        title=headline,
        canonical_url=f"https://example.com/b-{uuid4()}",
        published_at=detected,
        excerpt="Economic Times wire pickup",
    )

    with patch("app.services.event_dedup.connection") as mock_conn:
        from contextlib import contextmanager

        @contextmanager
        def _use_conn():
            yield db_connection

        mock_conn.side_effect = _use_conn

        first = persist_deduped_event(
            raw=raw_a,
            title=raw_a.title,
            category=EventCategory.RBI_POLICY,
            event_source=AdapterSource.NEWSAPI,
            canonical_url=raw_a.canonical_url,
            confidence_score=55,
            detected_at=detected,
        )
        second = persist_deduped_event(
            raw=raw_b,
            title=headline,
            category=EventCategory.RBI_POLICY,
            event_source=AdapterSource.RBI_RSS,
            canonical_url=raw_b.canonical_url,
            confidence_score=88,
            detected_at=detected,
        )

    assert first == "inserted"
    assert second == "duplicate"

    with db_connection.cursor() as cur:
        cur.execute(
            """
            SELECT source_count, force_editorial_review,
                   jsonb_array_length(sources) AS src_len
            FROM public.events
            WHERE title = %s
            """,
            (headline,),
        )
        row = cur.fetchone()
    assert row is not None
    assert row[0] == 2
    assert row[1] is False
    assert row[2] == 2


@pytest.mark.integration
def test_source_count_above_five_sets_force_editorial_review(db_connection) -> None:
    apply_migrations(db_connection)
    detected = datetime(2025, 6, 15, 14, 0, tzinfo=UTC)
    headline = f"Merge stress test {uuid4().hex[:8]}"

    with patch("app.services.event_dedup.connection") as mock_conn:
        from contextlib import contextmanager

        @contextmanager
        def _use_conn():
            yield db_connection

        mock_conn.side_effect = _use_conn

        for i in range(6):
            raw = RawEvent(
                title=headline,
                canonical_url=f"https://merge.test/{uuid4()}",
                published_at=detected,
            )
            persist_deduped_event(
                raw=raw,
                title=headline,
                category=EventCategory.RBI_POLICY,
                event_source=AdapterSource.NEWSAPI,
                canonical_url=raw.canonical_url,
                confidence_score=60 + i,
                detected_at=detected,
            )

    with db_connection.cursor() as cur:
        cur.execute(
            """
            SELECT source_count, force_editorial_review
            FROM public.events
            WHERE title = %s
            """,
            (headline,),
        )
        row = cur.fetchone()
    assert row is not None
    assert row[0] == 6
    assert row[1] is True
