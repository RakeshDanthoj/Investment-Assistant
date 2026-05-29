"""P3-S1e: watchlist manual escalate creates draft event (G-05)."""

from __future__ import annotations

from uuid import UUID

import pytest

from app.db.migrate import apply_migrations
from app.services.watchlist import escalate_watchlist_item

SEED_ID = UUID("a1000001-0001-4001-8001-000000000001")


@pytest.mark.integration
def test_escalate_creates_event_with_watchlist_source(db_connection) -> None:
    apply_migrations(db_connection)

    with db_connection.cursor() as cur:
        cur.execute(
            """
            UPDATE public.watchlist_items
            SET status = 'watching', escalated_event_id = NULL
            WHERE id = %s
            """,
            (SEED_ID,),
        )
        cur.execute(
            """
            DELETE FROM public.events
            WHERE event_source = 'watchlist'
              AND canonical_url = %s
            """,
            (f"watchlist:{SEED_ID}",),
        )
        db_connection.commit()

    item, event_id = escalate_watchlist_item(SEED_ID)

    assert item["status"] == "escalated"
    assert item["escalated_event_id"] == str(event_id)

    with db_connection.cursor() as cur:
        cur.execute(
            """
            SELECT title, category, event_source, lifecycle_state
            FROM public.events
            WHERE id = %s
            """,
            (event_id,),
        )
        row = cur.fetchone()

    assert row is not None
    assert row[1] == "india_specific"
    assert row[2] == "watchlist"
    assert row[3] == "draft"
    assert "Maharashtra" in row[0]


@pytest.mark.integration
def test_migration_seeds_five_items(db_connection) -> None:
    apply_migrations(db_connection)
    with db_connection.cursor() as cur:
        cur.execute("SELECT count(*) FROM public.watchlist_items")
        count = cur.fetchone()[0]
    assert count >= 5


@pytest.mark.integration
def test_escalate_twice_returns_conflict_path(db_connection) -> None:
    apply_migrations(db_connection)

    with db_connection.cursor() as cur:
        cur.execute(
            """
            UPDATE public.watchlist_items
            SET status = 'watching', escalated_event_id = NULL
            WHERE id = %s
            """,
            (SEED_ID,),
        )
        cur.execute(
            "DELETE FROM public.events WHERE canonical_url = %s",
            (f"watchlist:{SEED_ID}",),
        )
        db_connection.commit()

    escalate_watchlist_item(SEED_ID)
    with pytest.raises(ValueError, match="already_escalated"):
        escalate_watchlist_item(SEED_ID)
