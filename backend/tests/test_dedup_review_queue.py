"""P3-S1c: cross-category collision review queue (G-03)."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.db.migrate import apply_migrations
from app.models.enums import EventCategory
from app.services.event_dedup import persist_deduped_event
from app.sources.base import AdapterSource, RawEvent


@pytest.mark.integration
def test_cross_category_collision_queues_review(db_connection) -> None:
    apply_migrations(db_connection)
    detected = datetime(2025, 6, 15, 10, 30, tzinfo=UTC)
    headline = f"RBI policy signal {uuid4().hex[:8]}"

    with patch("app.services.event_dedup.connection") as mock_conn:
        from contextlib import contextmanager

        @contextmanager
        def _use_conn():
            yield db_connection

        mock_conn.side_effect = _use_conn

        persist_deduped_event(
            raw=RawEvent(
                title=headline,
                canonical_url=f"https://cross.test/rbi-{uuid4()}",
                published_at=detected,
            ),
            title=headline,
            category=EventCategory.RBI_POLICY,
            event_source=AdapterSource.RBI_RSS,
            canonical_url=f"https://cross.test/rbi-{uuid4()}",
            confidence_score=80,
            detected_at=detected,
        )
        persist_deduped_event(
            raw=RawEvent(
                title=headline,
                canonical_url=f"https://cross.test/reg-{uuid4()}",
                published_at=detected,
            ),
            title=headline,
            category=EventCategory.REGULATORY,
            event_source=AdapterSource.NEWSAPI,
            canonical_url=f"https://cross.test/reg-{uuid4()}",
            confidence_score=70,
            detected_at=detected,
        )

    with db_connection.cursor() as cur:
        cur.execute(
            """
            SELECT count(*) FROM public.dedup_review_queue
            WHERE reason = 'cross_category_same_window'
              AND status = 'pending'
            """
        )
        pending = cur.fetchone()[0]
        cur.execute(
            """
            SELECT event_ids FROM public.dedup_review_queue
            WHERE reason = 'cross_category_same_window'
            ORDER BY created_at DESC
            LIMIT 1
            """
        )
        row = cur.fetchone()

    assert pending >= 1
    assert row is not None
    assert len(row[0]) == 2


@pytest.mark.integration
def test_cross_category_events_are_not_auto_merged(db_connection) -> None:
    apply_migrations(db_connection)
    detected = datetime(2025, 6, 15, 10, 30, tzinfo=UTC)
    headline = f"No auto merge {uuid4().hex[:8]}"

    with patch("app.services.event_dedup.connection") as mock_conn:
        from contextlib import contextmanager

        @contextmanager
        def _use_conn():
            yield db_connection

        mock_conn.side_effect = _use_conn

        persist_deduped_event(
            raw=RawEvent(
                title=headline,
                canonical_url=f"https://nomerge.test/a-{uuid4()}",
                published_at=detected,
            ),
            title=headline,
            category=EventCategory.RBI_POLICY,
            event_source=AdapterSource.RBI_RSS,
            canonical_url=f"https://nomerge.test/a-{uuid4()}",
            confidence_score=80,
            detected_at=detected,
        )
        persist_deduped_event(
            raw=RawEvent(
                title=headline,
                canonical_url=f"https://nomerge.test/b-{uuid4()}",
                published_at=detected,
            ),
            title=headline,
            category=EventCategory.MACRO,
            event_source=AdapterSource.NEWSAPI,
            canonical_url=f"https://nomerge.test/b-{uuid4()}",
            confidence_score=70,
            detected_at=detected,
        )

    with db_connection.cursor() as cur:
        cur.execute(
            """
            SELECT count(*) FROM public.events
            WHERE title = %s
            """,
            (headline,),
        )
        total = cur.fetchone()[0]

    assert total == 2
