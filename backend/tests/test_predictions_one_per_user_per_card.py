"""One prediction per (user, card) returns 409 with prior value (P1-S12)."""

from uuid import uuid4

import pytest

from app.db.migrate import apply_migrations
from app.services.predictions import DuplicatePredictionError, PredictionError, log


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


def _insert_card(cur, *, event_id, card_id) -> None:
    canon = f"pytest:{uuid4()}@example.invalid"
    cur.execute(
        """
        INSERT INTO public.events (
          id, title, category, confidence_score, lifecycle_state,
          canonical_url, event_source
        )
        VALUES (%s::uuid, %s, 'macro'::event_category, 55, 'published', %s, 'pytest')
        """,
        (str(event_id), "Pytest prediction event", canon),
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


def test_duplicate_prediction_raises_with_prior_text(db_connection) -> None:
    user_id = uuid4()
    event_id = uuid4()
    card_id = uuid4()
    first_text = "Primary thesis unfolds - mechanisms align with the stated horizon."
    second_text = "Thesis weakens - a key assumption breaks earlier than modeled."

    try:
        with db_connection.cursor() as cur:
            _insert_auth_user(cur, user_id, f"pytest-{user_id}@example.invalid")
            _insert_card(cur, event_id=event_id, card_id=card_id)
        db_connection.commit()

        log(user_id=user_id, card_id=card_id, prediction_text=first_text)

        with pytest.raises(DuplicatePredictionError) as exc_info:
            log(user_id=user_id, card_id=card_id, prediction_text=second_text)

        assert exc_info.value.prediction_text == first_text
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


def test_unknown_card_raises_not_found(db_connection) -> None:
    user_id = uuid4()
    card_id = uuid4()

    try:
        with db_connection.cursor() as cur:
            _insert_auth_user(cur, user_id, f"pytest-{user_id}@example.invalid")
        db_connection.commit()

        with pytest.raises(PredictionError, match="card_not_found"):
            log(
                user_id=user_id,
                card_id=card_id,
                prediction_text="Structured view - thesis confirms within horizon",
            )
    finally:
        db_connection.rollback()
        with db_connection.cursor() as cur:
            cur.execute("DELETE FROM auth.users WHERE id = %s::uuid", (str(user_id),))
        db_connection.commit()
