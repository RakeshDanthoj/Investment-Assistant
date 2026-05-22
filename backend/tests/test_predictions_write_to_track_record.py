"""Prediction logging dual-writes user_predictions and track_record (P1-S12)."""

from uuid import uuid4

import pytest

from app.db.migrate import apply_migrations
from app.services.predictions import log


@pytest.fixture(scope="module", autouse=True)
def ensure_migrations(db_connection):
    apply_migrations(db_connection)


def _insert_auth_user(cur, user_id, email: str) -> None:
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


def test_log_writes_user_predictions_and_track_record(db_connection) -> None:
    user_id = uuid4()
    event_id = uuid4()
    card_id = uuid4()
    prediction_text = "Mixed - competing mechanisms cancel; outcome stays ambiguous."
    canon = f"pytest:{uuid4()}@example.invalid"

    try:
        with db_connection.cursor() as cur:
            _insert_auth_user(cur, user_id, f"pytest-{user_id}@example.invalid")
            cur.execute(
                """
                INSERT INTO public.events (
                  id, title, category, confidence_score, lifecycle_state,
                  canonical_url, event_source
                )
                VALUES (%s::uuid, %s, 'macro'::event_category, 55, 'published', %s, 'pytest')
                """,
                (str(event_id), "Pytest dual-write event", canon),
            )
            cur.execute(
                """
                INSERT INTO public.cards (
                  id, event_id, title, insight_layer, context_layer, evidence_layer,
                  dissenting_view, framework_behind_this, prompt_version, lifecycle_state
                )
                VALUES (
                  %s::uuid, %s::uuid, 'Pytest card', 'Body [MEASURED]', 'Ctx [MEASURED]',
                  '{}'::jsonb, 'Dissent [MEASURED]', 'Fw [MEASURED]', 'pytest', 'published'
                )
                """,
                (str(card_id), str(event_id)),
            )
        db_connection.commit()

        log(user_id=user_id, card_id=card_id, prediction_text=prediction_text)

        with db_connection.cursor() as cur:
            cur.execute(
                """
                SELECT prediction_text
                FROM public.user_predictions
                WHERE user_id = %s::uuid AND card_id = %s::uuid
                """,
                (str(user_id), str(card_id)),
            )
            row = cur.fetchone()
            assert row is not None
            assert row[0] == prediction_text

            cur.execute(
                """
                SELECT payload
                FROM public.track_record
                WHERE card_id = %s::uuid
                ORDER BY logged_at DESC
                LIMIT 1
                """,
                (str(card_id),),
            )
            tr_row = cur.fetchone()
            assert tr_row is not None
            payload = tr_row[0]
            assert isinstance(payload, dict)
            assert payload.get("kind") == "user_prediction"
            assert payload.get("user_id") == str(user_id)
            assert payload.get("prediction_text") == prediction_text
            assert payload.get("source") == "prediction_logger"
    finally:
        db_connection.rollback()
        with db_connection.cursor() as cur:
            cur.execute(
                "DELETE FROM public.user_predictions WHERE card_id = %s::uuid",
                (str(card_id),),
            )
            cur.execute("DELETE FROM public.cards WHERE id = %s::uuid", (str(card_id),))
            cur.execute("DELETE FROM public.events WHERE id = %s::uuid", (str(event_id),))
            cur.execute("DELETE FROM auth.users WHERE id = %s::uuid", (str(user_id),))
        db_connection.commit()
