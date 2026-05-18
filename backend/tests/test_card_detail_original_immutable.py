"""Original Thread view reads immutable publish snapshot from track_record (P1-S10)."""

from uuid import uuid4

import pytest

from app.db.migrate import apply_migrations
from app.services.card_detail import build_card_detail
from app.services.publish_card import publish_draft_card


@pytest.fixture(scope="module", autouse=True)
def ensure_migrations(db_connection):
    apply_migrations(db_connection)


def test_original_view_keeps_day_one_copy_while_current_mutates(db_connection):
    event_id = uuid4()
    card_id = uuid4()
    canon = f"pytest:{uuid4()}@example.invalid"

    try:
        with db_connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.events (
                  id, title, category, confidence_score, lifecycle_state,
                  canonical_url, event_source
                )
                VALUES (%s, %s, 'macro'::event_category, 55, 'draft',
                  %s, 'pytest')
                """,
                (str(event_id), "Pytest detail event", canon),
            )
            cur.execute(
                """
                INSERT INTO public.cards (
                  id, event_id, title, insight_layer, context_layer, evidence_layer,
                  dissenting_view, framework_behind_this, prompt_version, lifecycle_state
                )
                VALUES (
                  %s, %s, 'Day one title', 'Insight [MEASURED] v1',
                  '1. Step one [MEASURED]',
                  '{"markdown":"MD [MODELLED]","sources":[]}'::jsonb,
                  'Dissent body [JUDGED]',
                  'Framework text',
                  'pytest', 'draft'
                )
                """,
                (str(card_id), str(event_id)),
            )
        db_connection.commit()

        publish_draft_card(card_id)

        current_before = build_card_detail(card_id, view="current")
        original_before = build_card_detail(card_id, view="original")
        assert current_before is not None and original_before is not None
        assert current_before["title"] == original_before["title"] == "Day one title"

        with db_connection.cursor() as cur:
            cur.execute(
                """
                UPDATE public.cards
                SET title = %s, insight_layer = %s, updated_at = now()
                WHERE id = %s
                """,
                ("Edited title", "Insight [MEASURED] v2", str(card_id)),
            )
        db_connection.commit()

        current_after = build_card_detail(card_id, view="current")
        original_after = build_card_detail(card_id, view="original")
        assert current_after is not None and original_after is not None
        assert current_after["title"] == "Edited title"
        assert current_after["insight_layer"] == "Insight [MEASURED] v2"
        assert original_after["title"] == "Day one title"
        assert original_after["insight_layer"] == "Insight [MEASURED] v1"

    finally:
        db_connection.rollback()
        with db_connection.cursor() as cur:
            cur.execute("DELETE FROM public.in_app_notifications WHERE card_id = %s", (str(card_id),))
            cur.execute("DELETE FROM public.cards WHERE id = %s", (str(card_id),))
            cur.execute("DELETE FROM public.events WHERE id = %s", (str(event_id),))
        db_connection.commit()


def test_original_view_missing_returns_none(db_connection):
    unknown = uuid4()
    assert build_card_detail(unknown, view="original") is None
