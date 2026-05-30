"""P3-T4: Editorial integrity verification gate (G-07, G-09, G-15).

Proves publish is impossible until number validation and checklist pass,
and section regen cannot bypass the validator before FoW work (P3-S1l).

Frontend publish-button disable is covered by
``frontend/app/admin/review/_components/ChecklistPanel.test.tsx``.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.db.migrate import apply_migrations
from app.main import app
from app.services.card_regen import regenerate_section
from app.services.editorial_checklist import DISSENT_MIN_CHARS

_LONG_DISSENT = "x" * (DISSENT_MIN_CHARS + 1)
_FRESH_RETRIEVED = datetime(2025, 6, 1, 12, 0, tzinfo=UTC).isoformat()


@pytest.fixture(scope="module", autouse=True)
def ensure_migrations(db_connection):
    apply_migrations(db_connection)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _grounded_evidence_layer(*, include_99_9: bool = False) -> dict:
    markdown = "sensitivity for hdfcbank on crude_oil axis is -4 per factor database snapshot."
    if include_99_9:
        markdown = f"analyst consensus at 99.9% certainty; {markdown}"
    return {
        "markdown": markdown,
        "sources": [
            {
                "id": "src-1",
                "source_url": "https://example.com/factor-db",
                "retrieved_at": _FRESH_RETRIEVED,
                "mmj_tag": "MEASURED",
                "source_excerpt": markdown,
            }
        ],
        "matrix_snapshot": {
            "sector": {"slug": "banking", "name": "Banking"},
            "factors": [],
            "instruments": [],
            "sensitivities": {
                "HDFCBANK": {
                    "crude_oil": {
                        "sensitivity": -4,
                        "mmj_tag": "MEASURED",
                        "source_url": "https://example.com/src",
                        "retrieved_at": _FRESH_RETRIEVED,
                        "freshness": "green",
                    }
                }
            },
        },
    }


def _insert_draft_card(
    db_connection,
    *,
    insight: str,
    context: str = "Context explains transmission mechanics [JUDGED].",
    evidence_layer: dict | None = None,
) -> tuple[str, str]:
    event_id = uuid4()
    card_id = uuid4()
    canon = f"pytest:{uuid4()}@example.invalid"
    evidence = evidence_layer if evidence_layer is not None else _grounded_evidence_layer()
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
            (str(event_id), "Pytest editorial integrity event", canon),
        )
        cur.execute(
            """
            INSERT INTO public.cards (
              id, event_id, title, insight_layer, context_layer, evidence_layer,
              dissenting_view, framework_behind_this, prompt_version, lifecycle_state
            )
            VALUES (
              %s, %s, 'Pytest editorial card', %s, %s,
              %s::jsonb, %s, 'Framework notes [MEASURED].', 'pytest', 'draft'
            )
            """,
            (
                str(card_id),
                str(event_id),
                insight,
                context,
                json.dumps(evidence),
                _LONG_DISSENT,
            ),
        )
    db_connection.commit()
    return str(event_id), str(card_id)


def _update_evidence_layer(db_connection, card_id: str, evidence_layer: dict) -> None:
    with db_connection.cursor() as cur:
        cur.execute(
            """
            UPDATE public.cards
            SET evidence_layer = %s::jsonb, updated_at = now()
            WHERE id = %s
            """,
            (json.dumps(evidence_layer), card_id),
        )
    db_connection.commit()


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


class _BadInsightLlm:
    def complete_json(self, **kwargs):
        return (
            {"insight_layer": "Revised insight cites 99.9% upside potential [JUDGED]."},
            {"input_tokens": 40, "output_tokens": 60},
        )


def test_ungrounded_number_blocks_publish_with_422(
    client: TestClient, db_connection
) -> None:
    """14.1 — card with ungrounded number → GET shows FAIL + publish 422."""
    event_id, card_id = _insert_draft_card(
        db_connection,
        insight="Analysts cite 99.9% certainty on the outcome [JUDGED].",
        evidence_layer={
            "markdown": "factor sensitivity is -4 on crude axis only.",
            "sources": [
                {
                    "id": "src-1",
                    "source_url": "https://example.com/report",
                    "retrieved_at": _FRESH_RETRIEVED,
                    "mmj_tag": "MEASURED",
                    "source_excerpt": "sensitivity is -4 on crude axis",
                }
            ],
        },
    )
    try:
        detail_resp = client.get(f"/api/admin/cards/{card_id}")
        assert detail_resp.status_code == 200
        body = detail_resp.json()
        assert body["number_validation"]["status"] == "FAIL"
        assert body["number_validation"]["ungrounded"]
        assert body["editorial_checklist"]["all_automated_pass"] is False
        numbers_item = next(
            item for item in body["editorial_checklist"]["items"] if item["key"] == "numbers"
        )
        assert numbers_item["status"] == "FAIL"

        publish_resp = client.post(
            f"/api/admin/cards/{card_id}/publish",
            json={"editor_review_seconds": 30, "plain_english_confirmed": True},
        )
        assert publish_resp.status_code == 422
        detail = publish_resp.json()["detail"]
        assert detail["code"] == "number_validator_failed"
        assert detail["status"] == "FAIL"
        assert detail["ungrounded"]
    finally:
        _cleanup(db_connection, event_id, card_id)


def test_happy_path_evidence_fix_checklist_then_publish_200(
    client: TestClient, db_connection
) -> None:
    """14.2 — fix Evidence → validator PASS → auto checklist PASS → publish 200."""
    event_id, card_id = _insert_draft_card(
        db_connection,
        insight="Analysts cite 99.9% certainty on the outcome [JUDGED].",
        evidence_layer={
            "markdown": "factor sensitivity is -4 on crude axis only.",
            "sources": [
                {
                    "id": "src-1",
                    "source_url": "https://example.com/report",
                    "retrieved_at": _FRESH_RETRIEVED,
                    "mmj_tag": "MEASURED",
                    "source_excerpt": "sensitivity is -4 on crude axis",
                }
            ],
        },
    )
    try:
        blocked = client.post(
            f"/api/admin/cards/{card_id}/publish",
            json={"editor_review_seconds": 30, "plain_english_confirmed": True},
        )
        assert blocked.status_code == 422
        assert blocked.json()["detail"]["code"] == "number_validator_failed"

        _update_evidence_layer(
            db_connection,
            card_id,
            _grounded_evidence_layer(include_99_9=True),
        )

        detail_resp = client.get(f"/api/admin/cards/{card_id}")
        assert detail_resp.status_code == 200
        body = detail_resp.json()
        assert body["number_validation"]["status"] == "PASS"
        assert body["editorial_checklist"]["all_automated_pass"] is True
        automated = [item for item in body["editorial_checklist"]["items"] if item["automated"]]
        assert len(automated) == 4
        assert all(item["status"] == "PASS" for item in automated)

        without_manual = client.post(
            f"/api/admin/cards/{card_id}/publish",
            json={"editor_review_seconds": 45, "plain_english_confirmed": False},
        )
        assert without_manual.status_code == 422
        assert without_manual.json()["detail"]["code"] == "publish_rejected"

        publish_resp = client.post(
            f"/api/admin/cards/{card_id}/publish",
            json={"editor_review_seconds": 45, "plain_english_confirmed": True},
        )
        assert publish_resp.status_code == 200
        assert publish_resp.json()["lifecycle_state"] == "published"

        published = client.get(f"/api/admin/cards/{card_id}")
        assert published.status_code == 200
        assert published.json()["lifecycle_state"] == "published"
    finally:
        _cleanup(db_connection, event_id, card_id)


@patch("app.services.card_regen.validate_numbers_in_evidence")
@patch("app.services.card_regen.consume_slot_or_raise")
@patch("app.services.card_regen.check_monthly_budget_or_raise")
def test_section_regen_cannot_bypass_validator(
    mock_budget,
    mock_consume,
    mock_validate_numbers,
    client: TestClient,
    db_connection,
) -> None:
    """14.3 — regen introduces ungrounded number → publish still blocked."""
    mock_validate_numbers.return_value = None
    event_id, card_id = _insert_draft_card(
        db_connection,
        insight="The matrix flags about -4 on crude for this name [MEASURED].",
    )
    try:
        before = client.get(f"/api/admin/cards/{card_id}")
        assert before.json()["number_validation"]["status"] == "PASS"

        regen_result = regenerate_section(
            card_id,
            section="insight",
            editor_note="Sharpen the lead with a stronger claim.",
            llm=_BadInsightLlm(),
        )
        assert regen_result.post_check.number_validation.status == "FAIL"

        after = client.get(f"/api/admin/cards/{card_id}")
        assert after.json()["number_validation"]["status"] == "FAIL"
        assert after.json()["editorial_checklist"]["all_automated_pass"] is False

        publish_resp = client.post(
            f"/api/admin/cards/{card_id}/publish",
            json={"editor_review_seconds": 60, "plain_english_confirmed": True},
        )
        assert publish_resp.status_code == 422
        assert publish_resp.json()["detail"]["code"] == "number_validator_failed"
    finally:
        _cleanup(db_connection, event_id, card_id)
