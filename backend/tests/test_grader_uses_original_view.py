"""Grader must use Original View (initial_publish), not live card alone (P2-S2)."""

import json
from uuid import uuid4

import pytest

from app.db.migrate import apply_migrations
from app.jobs.grade_on_resolve import grade_predictions_for_card, transition_card_to_resolved
from app.services.predictions import log


class _RecordingGraderLlm:
    def __init__(self) -> None:
        self.original_insight: str | None = None
        self.final_insight: str | None = None

    def complete_json(self, *, system: str, user: str, prompt_version: str, max_tokens: int = 4096):
        del system, prompt_version, max_tokens
        import json

        marker = "## Grading payload"
        idx = user.find(marker)
        blob = user[idx + len(marker) :].strip() if idx >= 0 else user
        payload = json.loads(blob)
        self.original_insight = payload["original_view"]["insight_layer"]
        self.final_insight = payload["final_card_state"]["insight_layer"]
        return {
            "mechanism_accuracy": "correct",
            "business_accuracy": "partial",
            "market_accuracy": "incorrect",
            "gap_insight": (
                "You underweighted the duration channel that the Original View emphasised "
                "while overweighting a generic liquidity narrative in your call."
            ),
        }, {"input_tokens": 1, "output_tokens": 1}


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


def test_grade_on_resolve_idempotent_and_uses_original_view(db_connection) -> None:
    user_id = uuid4()
    event_id = uuid4()
    card_id = uuid4()
    canon = f"pytest-grade:{uuid4()}@example.invalid"
    recorder = _RecordingGraderLlm()

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
                (str(event_id), "Grader pytest event", canon),
            )
            cur.execute(
                """
                INSERT INTO public.cards (
                  id, event_id, title, insight_layer, context_layer, evidence_layer,
                  dissenting_view, framework_behind_this, prompt_version, lifecycle_state
                )
                VALUES (
                  %s::uuid, %s::uuid, 'Grader card', 'LIVE insight [MEASURED]', 'Live ctx [MEASURED]',
                  '{}'::jsonb, 'Dissent [MEASURED]', 'Fw [MEASURED]', 'pytest', 'active'
                )
                """,
                (str(card_id), str(event_id)),
            )
            publish_payload = {
                "kind": "initial_publish",
                "card_title": "Grader card",
                "ice_snapshot": {
                    "title": "Grader card",
                    "insight_layer": "DAY_ONE_ORIGINAL_INSIGHT [MEASURED]",
                    "context_layer": "Day one context [MEASURED]",
                },
            }
            cur.execute(
                """
                INSERT INTO public.track_record (card_id, payload)
                VALUES (%s::uuid, %s::jsonb)
                """,
                (str(card_id), json.dumps(publish_payload)),
            )
        db_connection.commit()

        log(
            user_id=user_id,
            card_id=card_id,
            prediction_text="Liquidity stress will dominate before fundamentals reprice.",
        )

        transition_card_to_resolved(card_id, llm=recorder)
        assert recorder.original_insight == "DAY_ONE_ORIGINAL_INSIGHT [MEASURED]"
        assert recorder.final_insight == "LIVE insight [MEASURED]"

        first = grade_predictions_for_card(card_id, llm=recorder)
        assert first == 0

        with db_connection.cursor() as cur:
            cur.execute(
                """
                SELECT mechanism_accuracy, business_accuracy, market_accuracy, gap_insight
                FROM public.user_predictions
                WHERE user_id = %s::uuid AND card_id = %s::uuid
                """,
                (str(user_id), str(card_id)),
            )
            row = cur.fetchone()
            assert row is not None
            assert row[0] == "correct"
            assert row[1] == "partial"
            assert row[2] == "incorrect"
            assert "duration channel" in (row[3] or "").lower()

            cur.execute(
                """
                SELECT COUNT(*) FROM public.track_record
                WHERE card_id = %s::uuid AND payload->>'kind' = 'prediction_grade'
                """,
                (str(card_id),),
            )
            assert int(cur.fetchone()[0]) == 1
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
