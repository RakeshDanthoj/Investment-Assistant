"""P3-T1: integration proof that synthetic rows never leak into Pulse, Thread, or Mirror (G-13)."""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import patch
from uuid import UUID, uuid4

import pytest

from app.db.migrate import apply_migrations
from app.db.synthetic_seed import seed_events
from app.services.card_detail import build_card_detail
from app.services.feed import build_feed_response
from app.services.mirror_predictions import list_predictions


@contextmanager
def _use_db_connection(db_connection):
    @contextmanager
    def _connection_override():
        yield db_connection

    with patch("app.db.synthetic_seed.connection", _connection_override):
        with patch("app.db.connection.connection", _connection_override):
            with patch("app.services.feed.connection", _connection_override):
                with patch("app.services.card_repository.connection", _connection_override):
                    with patch(
                        "app.services.mirror_predictions.connection",
                        _connection_override,
                    ):
                        yield


@pytest.fixture(scope="module")
def synthetic_seed(db_connection):
    apply_migrations(db_connection)
    with _use_db_connection(db_connection):
        result = seed_events(apply_migration=False)
    assert result["total"] == 20
    return db_connection


def _synthetic_event_ids(conn) -> set[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT id::text FROM public.events WHERE is_synthetic = TRUE")
        return {row[0] for row in cur.fetchall()}


def _insert_auth_user(cur, user_id: UUID, email: str) -> None:
    cur.execute(
        """
        INSERT INTO auth.users (
          instance_id, id, aud, role, email,
          encrypted_password, email_confirmed_at,
          created_at, updated_at
        )
        VALUES (
          '00000000-0000-0000-0000-000000000000',
          %s::uuid, 'authenticated', 'authenticated', %s,
          crypt('pytest-pass', gen_salt('bf')), now(), now(), now()
        )
        ON CONFLICT (id) DO NOTHING
        """,
        (str(user_id), email),
    )


def _create_card_on_synthetic_event(conn) -> tuple[UUID, str]:
    """Published card on a seeded synthetic event (must not surface in user reads)."""
    card_id = uuid4()
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT id::text
            FROM public.events
            WHERE is_synthetic = TRUE
            ORDER BY created_at
            LIMIT 1
            """
        )
        row = cur.fetchone()
        if not row:
            pytest.fail("expected seeded synthetic events")
        event_id = row[0]
        cur.execute(
            """
            INSERT INTO public.cards (
              id, event_id, title, insight_layer, context_layer, evidence_layer,
              dissenting_view, framework_behind_this, prompt_version, lifecycle_state
            )
            VALUES (
              %s::uuid, %s::uuid,
              'P3-T1 synthetic isolation probe',
              'Probe insight [MEASURED]', 'Probe context [MEASURED]',
              '{}'::jsonb, 'Probe dissent [MEASURED]', 'Probe framework [MEASURED]',
              'p3-t1-isolation', 'published'::public.lifecycle_state
            )
            """,
            (str(card_id), event_id),
        )
    conn.commit()
    return card_id, event_id


@pytest.mark.integration
def test_pulse_feed_excludes_synthetic_events(synthetic_seed) -> None:
    conn = synthetic_seed
    synthetic_ids = _synthetic_event_ids(conn)
    assert len(synthetic_ids) == 20

    with _use_db_connection(conn):
        feed = build_feed_response(session_id=None, horizon=None, category=None)

    for item in feed.get("items") or []:
        event_id = item.get("event_id")
        assert event_id not in synthetic_ids, "Pulse feed leaked a synthetic event_id"


@pytest.mark.integration
def test_thread_detail_excludes_synthetic_event_cards(synthetic_seed) -> None:
    conn = synthetic_seed
    card_id, event_id = _create_card_on_synthetic_event(conn)
    assert event_id in _synthetic_event_ids(conn)

    try:
        with _use_db_connection(conn):
            detail = build_card_detail(card_id, view="current")
        assert detail is None, "Thread detail must not return cards on synthetic events"
    finally:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM public.cards WHERE id = %s::uuid", (str(card_id),))
        conn.commit()


@pytest.mark.integration
def test_mirror_predictions_exclude_synthetic_rows(synthetic_seed) -> None:
    conn = synthetic_seed
    user_id = uuid4()
    card_id, event_id = _create_card_on_synthetic_event(conn)

    try:
        with conn.cursor() as cur:
            _insert_auth_user(cur, user_id, f"p3-t1-{user_id}@example.invalid")
            cur.execute(
                """
                INSERT INTO public.user_predictions (
                  user_id, card_id, prediction_text, is_synthetic
                )
                VALUES (%s::uuid, %s::uuid, %s, TRUE)
                """,
                (
                    str(user_id),
                    str(card_id),
                    "Synthetic probe prediction — must not appear in Mirror",
                ),
            )
        conn.commit()

        with _use_db_connection(conn):
            rows = list_predictions(user_id)

        assert all(r.card_id != card_id for r in rows), "Mirror leaked synthetic prediction"
        assert event_id in _synthetic_event_ids(conn)
    finally:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM public.user_predictions WHERE card_id = %s::uuid",
                (str(card_id),),
            )
            cur.execute("DELETE FROM public.cards WHERE id = %s::uuid", (str(card_id),))
        conn.commit()


@pytest.mark.integration
def test_service_role_direct_query_can_read_synthetic_events(synthetic_seed) -> None:
    """Smoke: postgres/service connection bypasses RLS and sees seeded synthetic rows."""
    conn = synthetic_seed
    with conn.cursor() as cur:
        cur.execute("SELECT count(*) FROM public.events WHERE is_synthetic = TRUE")
        total = cur.fetchone()[0]
        cur.execute(
            """
            SELECT count(*) FROM public.events
            WHERE is_synthetic = TRUE AND is_major = TRUE
            """
        )
        major = cur.fetchone()[0]

    assert total == 20
    assert major == 7
