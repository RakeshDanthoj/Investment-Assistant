"""P3-T2: Data pipeline integration test gate (G-03, G-04, G-05, G-06)."""

from __future__ import annotations

import contextlib
from contextlib import contextmanager
from datetime import UTC, datetime
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest

from app.db.migrate import apply_migrations
from app.models.enums import EventCategory
from app.services.card_pipeline import draft_card_from_event
from app.services.event_dedup import persist_deduped_event
from app.services.market_facts_adapters import CriticalFactsHoldError
from app.services.newsapi_config import FactorKeywordSet, NewsApiSchedulerConfig
from app.services.newsapi_scheduler import resolve_next_factor
from app.services.watchlist import escalate_watchlist_item
from app.sources.base import AdapterSource, RawEvent

WATCHLIST_SEED_ID = UUID("a1000001-0001-4001-8001-000000000001")


@contextmanager
def _use_db_connection(db_connection):
    @contextmanager
    def _connection_override():
        yield db_connection

    patches = (
        "app.db.connection.connection",
        "app.services.event_dedup.connection",
        "app.services.watchlist.connection",
        "app.services.card_repository.connection",
        "app.services.pipeline_telemetry.connection",
        "app.services.cost_guard.connection",
    )
    with contextlib.ExitStack() as stack:
        for target in patches:
            stack.enter_context(patch(target, _connection_override))
        yield


def _eight_factor_config() -> NewsApiSchedulerConfig:
    factors = tuple(
        FactorKeywordSet(slug=slug, daily_calls=budget, keywords=(slug.replace("_", " "),))
        for slug, budget in (
            ("crude_oil", 2),
            ("dollar_rupee", 1),
            ("domestic_interest_rates", 1),
            ("global_risk_sentiment", 1),
            ("monsoon_index", 1),
            ("government_capex", 1),
            ("gst_collections_trend", 1),
            ("sector_regulatory_environment", 1),
        )
    )
    return NewsApiSchedulerConfig(mode="round_robin", max_daily_calls=9, factors=factors)


def _editorial_draft_event_ids(db_connection, *, event_source: str | None = None) -> set[str]:
    clauses = ["lifecycle_state = 'draft'"]
    params: list[object] = []
    if event_source:
        clauses.append("event_source = %s")
        params.append(event_source)
    sql = f"SELECT id::text FROM public.events WHERE {' AND '.join(clauses)}"
    with db_connection.cursor() as cur:
        cur.execute(sql, tuple(params))
        return {row[0] for row in cur.fetchall()}


@pytest.mark.integration
def test_three_duplicate_ingests_merge_to_one_event_with_source_count_three(
    db_connection,
) -> None:
    """7.1 — same story from three outlets → one row, source_count = 3."""
    apply_migrations(db_connection)
    detected = datetime(2025, 6, 15, 10, 30, tzinfo=UTC)
    headline = f"P3-T2 dedup merge {uuid4().hex[:8]}"
    sources = (
        (AdapterSource.NEWSAPI, f"https://example.com/a-{uuid4()}"),
        (AdapterSource.RBI_RSS, f"https://example.com/b-{uuid4()}"),
        (AdapterSource.NSE_BSE, f"https://example.com/c-{uuid4()}"),
    )

    try:
        with _use_db_connection(db_connection):
            outcomes = []
            for event_source, canonical_url in sources:
                raw = RawEvent(
                    title=headline,
                    canonical_url=canonical_url,
                    published_at=detected,
                )
                outcomes.append(
                    persist_deduped_event(
                        raw=raw,
                        title=headline,
                        category=EventCategory.RBI_POLICY,
                        event_source=event_source,
                        canonical_url=canonical_url,
                        confidence_score=60,
                        detected_at=detected,
                    )
                )

        assert outcomes == ["inserted", "duplicate", "duplicate"]

        with db_connection.cursor() as cur:
            cur.execute(
                """
                SELECT count(*)::int, max(source_count), max(jsonb_array_length(sources))
                FROM public.events
                WHERE title = %s
                """,
                (headline,),
            )
            row_count, source_count, sources_len = cur.fetchone()

        assert row_count == 1
        assert source_count == 3
        assert sources_len == 3
    finally:
        with db_connection.cursor() as cur:
            cur.execute("DELETE FROM public.events WHERE title = %s", (headline,))
        db_connection.rollback()


def test_newsapi_eight_factor_rotation_respects_daily_cap() -> None:
    """7.2 — mock 8-factor round-robin completes without exceeding per-factor budgets."""
    cfg = _eight_factor_config()
    assert len(cfg.factor_order) == 8

    counts: dict[str, int] = {}
    last: str | None = None
    ticks = 0
    while ticks < 20:
        slug = resolve_next_factor(last_polled_slug=last, counts_today=counts, config=cfg)
        if slug is None:
            break
        counts[slug] = counts.get(slug, 0) + 1
        last = slug
        ticks += 1

    assert ticks == cfg.max_daily_calls
    for factor_slug, budget in cfg.daily_budgets.items():
        assert counts.get(factor_slug, 0) <= budget
    assert sum(counts.values()) == cfg.max_daily_calls


@pytest.mark.integration
def test_watchlist_escalated_event_visible_in_editorial_draft_queue(db_connection) -> None:
    """7.3 — escalate creates a draft event visible in the editorial queue filter."""
    apply_migrations(db_connection)

    try:
        with db_connection.cursor() as cur:
            cur.execute(
                """
                UPDATE public.watchlist_items
                SET status = 'watching', escalated_event_id = NULL
                WHERE id = %s
                """,
                (WATCHLIST_SEED_ID,),
            )
            cur.execute(
                "DELETE FROM public.events WHERE canonical_url = %s",
                (f"watchlist:{WATCHLIST_SEED_ID}",),
            )
            db_connection.commit()

        with _use_db_connection(db_connection):
            _item, event_id = escalate_watchlist_item(WATCHLIST_SEED_ID)

        draft_watchlist_ids = _editorial_draft_event_ids(db_connection, event_source="watchlist")
        assert str(event_id) in draft_watchlist_ids
    finally:
        with db_connection.cursor() as cur:
            cur.execute(
                """
                UPDATE public.watchlist_items
                SET status = 'watching', escalated_event_id = NULL
                WHERE id = %s
                """,
                (WATCHLIST_SEED_ID,),
            )
            cur.execute(
                "DELETE FROM public.events WHERE canonical_url = %s",
                (f"watchlist:{WATCHLIST_SEED_ID}",),
            )
        db_connection.rollback()


@pytest.mark.integration
def test_unavailable_critical_fact_records_held_pipeline_run(db_connection) -> None:
    """7.4 — unavailable critical fact blocks card draft and records held pipeline status."""
    apply_migrations(db_connection)
    event_id = uuid4()
    headline = f"P3-T2 critical hold {uuid4().hex[:8]}"

    try:
        with db_connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.events (
                  id, title, category, source_url, canonical_url, event_source,
                  confidence_score, lifecycle_state
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    event_id,
                    headline,
                    EventCategory.RBI_POLICY.value,
                    f"https://hold.test/{event_id}",
                    f"https://hold.test/{event_id}",
                    "integration_test",
                    70,
                    "draft",
                ),
            )
            db_connection.commit()

        with (
            _use_db_connection(db_connection),
            patch(
                "app.services.card_pipeline.assert_critical_facts_available",
                side_effect=CriticalFactsHoldError(["inr_usd"]),
            ),
            pytest.raises(CriticalFactsHoldError),
        ):
            draft_card_from_event(event_id)

        with db_connection.cursor() as cur:
            cur.execute(
                """
                SELECT status, context->>'event_id' AS event_id
                FROM public.pipeline_runs
                WHERE pipeline = 'card_draft'
                  AND status = 'held'
                  AND context->>'event_id' = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (str(event_id),),
            )
            held_row = cur.fetchone()
            cur.execute(
                "SELECT count(*)::int FROM public.cards WHERE event_id = %s",
                (event_id,),
            )
            card_count = cur.fetchone()[0]

        assert held_row is not None
        assert held_row[0] == "held"
        assert held_row[1] == str(event_id)
        assert card_count == 0
    finally:
        db_connection.rollback()
        with db_connection.cursor() as cur:
            cur.execute(
                "DELETE FROM public.pipeline_runs WHERE context->>'event_id' = %s",
                (str(event_id),),
            )
            cur.execute("DELETE FROM public.events WHERE id = %s", (event_id,))
        db_connection.commit()
