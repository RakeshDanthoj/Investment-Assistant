"""Publish workflow writes immutable track_record and transitions lifecycle (P1-S8)."""

from uuid import uuid4

import pytest

from app.db.migrate import apply_migrations
from app.services.publish_card import PublishCardError, publish_draft_card


@pytest.fixture(scope="module", autouse=True)
def ensure_migrations(db_connection):
    apply_migrations(db_connection)


def test_publish_writes_track_record_and_sets_lifecycle(db_connection):
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
                (str(event_id), "Pytest publish event", canon),
            )
            cur.execute(
                """
                INSERT INTO public.cards (
                  id, event_id, title, insight_layer, context_layer, evidence_layer,
                  dissenting_view, framework_behind_this, prompt_version, lifecycle_state
                )
                VALUES (
                  %s, %s, 'Pytest card', 'Body [MEASURED]', 'Ctx [MEASURED]',
                  '{}'::jsonb, 'Dissent [MEASURED]', 'Fw [MEASURED]', 'pytest', 'draft'
                )
                """,
                (str(card_id), str(event_id)),
            )
        db_connection.commit()

        summary = publish_draft_card(card_id, editor_review_seconds=123)
        assert summary["lifecycle_state"] == "published"

        with db_connection.cursor() as cur:
            cur.execute(
                "SELECT lifecycle_state::text FROM public.cards WHERE id = %s",
                (str(card_id),),
            )
            assert cur.fetchone()[0] == "published"

            cur.execute(
                "SELECT lifecycle_state::text FROM public.events WHERE id = %s",
                (str(event_id),),
            )
            assert cur.fetchone()[0] == "published"

            cur.execute(
                "SELECT COUNT(*) FROM public.track_record WHERE card_id = %s",
                (str(card_id),),
            )
            assert cur.fetchone()[0] == 1

            cur.execute(
                "SELECT payload FROM public.track_record WHERE card_id = %s",
                (str(card_id),),
            )
            payload = cur.fetchone()[0]
            assert isinstance(payload, dict)
            assert payload.get("kind") == "initial_publish"
            assert payload.get("editor_review_seconds") == 123
            ice = payload.get("ice_snapshot")
            assert isinstance(ice, dict)
            assert ice.get("title") == "Pytest card"

        with pytest.raises(PublishCardError):
            publish_draft_card(card_id, editor_review_seconds=1)

    finally:
        with db_connection.cursor() as cur:
            cur.execute(
                "DELETE FROM public.in_app_notifications WHERE card_id = %s",
                (str(card_id),),
            )
            cur.execute("DELETE FROM public.cards WHERE id = %s", (str(card_id),))
            cur.execute("DELETE FROM public.events WHERE id = %s", (str(event_id),))
        db_connection.commit()
