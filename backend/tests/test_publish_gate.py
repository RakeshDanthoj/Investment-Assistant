"""Publish hard gate — number validator blocks 422 (P3-S1i)."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.db.migrate import apply_migrations
from app.main import app
from app.services.editorial_checklist import DISSENT_MIN_CHARS
from app.services.number_validator import NumberValidationFailedError
from app.services.publish_card import publish_draft_card

_LONG_DISSENT = "x" * (DISSENT_MIN_CHARS + 1)


@pytest.fixture(scope="module", autouse=True)
def ensure_migrations(db_connection):
    apply_migrations(db_connection)


def _insert_draft_card(
    db_connection,
    *,
    insight: str,
    context: str,
    evidence_layer: dict,
) -> tuple[str, str]:
    import json

    event_id = uuid4()
    card_id = uuid4()
    canon = f"pytest:{uuid4()}@example.invalid"
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
            (str(event_id), "Pytest publish gate event", canon),
        )
        cur.execute(
            """
            INSERT INTO public.cards (
              id, event_id, title, insight_layer, context_layer, evidence_layer,
              dissenting_view, framework_behind_this, prompt_version, lifecycle_state
            )
            VALUES (
              %s, %s, 'Pytest card', %s, %s,
              %s::jsonb, %s, 'Fw [MEASURED]', 'pytest', 'draft'
            )
            """,
            (
                str(card_id),
                str(event_id),
                insight,
                context,
                json.dumps(evidence_layer),
                _LONG_DISSENT,
            ),
        )
    db_connection.commit()
    return str(event_id), str(card_id)


def _cleanup(db_connection, event_id: str, card_id: str) -> None:
    db_connection.rollback()
    with db_connection.cursor() as cur:
        cur.execute(
            "DELETE FROM public.card_bias_flags WHERE card_id = %s",
            (card_id,),
        )
        cur.execute(
            "DELETE FROM public.in_app_notifications WHERE card_id = %s",
            (card_id,),
        )
        cur.execute("DELETE FROM public.cards WHERE id = %s", (card_id,))
        cur.execute("DELETE FROM public.events WHERE id = %s", (event_id,))
    db_connection.commit()


def test_publish_blocked_with_ungrounded_number(db_connection) -> None:
    event_id, card_id = _insert_draft_card(
        db_connection,
        insight="Analysts cite 99.9% certainty [JUDGED].",
        context="",
        evidence_layer={"markdown": "factor sensitivity is -4 on crude axis."},
    )
    try:
        with pytest.raises(NumberValidationFailedError) as exc_info:
            publish_draft_card(card_id)
        assert exc_info.value.result.status == "FAIL"
        assert exc_info.value.result.ungrounded

        client = TestClient(app)
        response = client.post(
            f"/api/admin/cards/{card_id}/publish",
            json={"editor_review_seconds": 30, "plain_english_confirmed": True},
        )
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert detail["code"] == "number_validator_failed"
        assert detail["status"] == "FAIL"
        assert detail["ungrounded"]
    finally:
        _cleanup(db_connection, event_id, card_id)


def test_publish_passes_when_evidence_grounds_numbers(db_connection) -> None:
    event_id, card_id = _insert_draft_card(
        db_connection,
        insight="The matrix flags about -4 on crude for this name [MEASURED].",
        context="",
        evidence_layer={
            "markdown": (
                "sensitivity for hdfcbank on crude_oil axis is -4 per factor database snapshot."
            ),
        },
    )
    try:
        summary = publish_draft_card(
            card_id,
            editor_review_seconds=45,
            plain_english_confirmed=True,
        )
        assert summary["lifecycle_state"] == "published"

        client = TestClient(app)
        response = client.get(f"/api/admin/cards/{card_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["number_validation"]["status"] == "PASS"
        assert body["editorial_checklist"]["all_automated_pass"] is True
    finally:
        _cleanup(db_connection, event_id, card_id)


def test_get_card_includes_number_validation(db_connection) -> None:
    event_id, card_id = _insert_draft_card(
        db_connection,
        insight="Body [MEASURED]",
        context="Ctx [MEASURED]",
        evidence_layer={},
    )
    try:
        client = TestClient(app)
        response = client.get(f"/api/admin/cards/{card_id}")
        assert response.status_code == 200
        validation = response.json()["number_validation"]
        assert validation["status"] == "PASS"
        assert "ungrounded" in validation
        assert "missing_provenance" in validation
        checklist = response.json()["editorial_checklist"]
        assert "items" in checklist
        assert "all_automated_pass" in checklist
    finally:
        _cleanup(db_connection, event_id, card_id)
