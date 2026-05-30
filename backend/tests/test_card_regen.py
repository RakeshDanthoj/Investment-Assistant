"""Targeted section regen + tiered full regen (P3-S1k)."""

from __future__ import annotations

import json
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.db.migrate import apply_migrations
from app.main import app
from app.services.card_regen import (
    FullRegenBlockedError,
    FullRegenConfirmRequiredError,
    regenerate_full,
    regenerate_section,
)
from app.services.editorial_checklist import DISSENT_MIN_CHARS

_LONG_DISSENT = "x" * (DISSENT_MIN_CHARS + 1)


@pytest.fixture(scope="module", autouse=True)
def ensure_migrations(db_connection):
    apply_migrations(db_connection)


def _matrix() -> dict:
    return {
        "sector": {"slug": "banking", "name": "Banking"},
        "factors": [],
        "instruments": [],
        "sensitivities": {
            "HDFCBANK": {
                "crude_oil": {
                    "sensitivity": -4,
                    "mmj_tag": "MEASURED",
                    "source_url": "https://example.com/src",
                    "retrieved_at": "2025-01-01T00:00:00+00:00",
                    "freshness": "green",
                }
            }
        },
    }


def _evidence_layer() -> dict:
    return {
        "markdown": "HDFCBANK | crude_oil | sensitivity=-4 | mmj=MEASURED",
        "macro_stub": "Macro stub",
        "matrix_snapshot": _matrix(),
        "event_snapshot": {"title": "Test event"},
    }


def _insert_draft_card(
    db_connection,
    *,
    full_regen_count: int = 0,
    po_regen_flag_cleared: bool = False,
) -> tuple[str, str]:
    event_id = uuid4()
    card_id = uuid4()
    canon = f"pytest:{uuid4()}@example.invalid"
    evidence = _evidence_layer()
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
            (str(event_id), "Pytest regen event", canon),
        )
        cur.execute(
            """
            INSERT INTO public.cards (
              id, event_id, title, insight_layer, context_layer, evidence_layer,
              dissenting_view, framework_behind_this, prompt_version, lifecycle_state,
              full_regen_count, po_regen_flag_cleared
            )
            VALUES (
              %s, %s, 'Pytest card',
              %s, %s, %s::jsonb, %s, %s, 'pytest', 'draft',
              %s, %s
            )
            """,
            (
                str(card_id),
                str(event_id),
                "Insight cites -4 sensitivity on HDFCBANK [MEASURED].",
                "Context repeats -4 from the matrix [MEASURED].",
                json.dumps(evidence),
                _LONG_DISSENT,
                "**Pattern**\n\nFramework body with enough length to pass validation checks.",
                full_regen_count,
                po_regen_flag_cleared,
            ),
        )
    db_connection.commit()
    return str(event_id), str(card_id)


def _cleanup(db_connection, event_id: str, card_id: str) -> None:
    db_connection.rollback()
    with db_connection.cursor() as cur:
        cur.execute("DELETE FROM public.instrument_assessments WHERE card_id = %s", (card_id,))
        cur.execute("DELETE FROM public.signals WHERE card_id = %s", (card_id,))
        cur.execute("DELETE FROM public.cards WHERE id = %s", (card_id,))
        cur.execute("DELETE FROM public.events WHERE id = %s", (event_id,))
    db_connection.commit()


def _fetch_layers(db_connection, card_id: str) -> dict[str, str]:
    with db_connection.cursor() as cur:
        cur.execute(
            """
            SELECT insight_layer, context_layer, dissenting_view, framework_behind_this,
                   evidence_layer::text, full_regen_count, regen_history::text
            FROM public.cards WHERE id = %s
            """,
            (card_id,),
        )
        row = cur.fetchone()
    assert row is not None
    return {
        "insight_layer": row[0],
        "context_layer": row[1],
        "dissenting_view": row[2],
        "framework_behind_this": row[3],
        "evidence_layer": row[4],
        "full_regen_count": str(row[5]),
        "regen_history": row[6],
    }


class _SectionLlm:
    def complete_json(self, **kwargs):
        return (
            {
                "insight_layer": (
                    "Revised insight still cites -4 sensitivity on HDFCBANK [MEASURED]."
                )
            },
            {"input_tokens": 40, "output_tokens": 60},
        )


@patch("app.services.card_regen.consume_slot_or_raise")
@patch("app.services.card_regen.check_monthly_budget_or_raise")
def test_section_regen_only_target_hash_changes(mock_budget, mock_consume, db_connection) -> None:
    event_id, card_id = _insert_draft_card(db_connection)
    try:
        before = _fetch_layers(db_connection, card_id)
        result = regenerate_section(
            card_id,
            section="insight",
            editor_note="Tighten the insight lead.",
            llm=_SectionLlm(),
        )
        after = _fetch_layers(db_connection, card_id)

        assert result.previous_hash != result.new_hash
        assert before["insight_layer"] != after["insight_layer"]
        assert before["context_layer"] == after["context_layer"]
        assert before["dissenting_view"] == after["dissenting_view"]
        assert before["framework_behind_this"] == after["framework_behind_this"]
        assert result.post_check.number_validation.status == "PASS"
        assert result.post_check.consistency_check["status"] == "PASS"
        history = json.loads(after["regen_history"])
        assert len(history) == 1
        assert history[0]["section"] == "insight"
        mock_consume.assert_called_once()
    finally:
        _cleanup(db_connection, event_id, card_id)


def test_full_regen_count_requires_confirm(db_connection) -> None:
    event_id, card_id = _insert_draft_card(db_connection, full_regen_count=1)
    try:
        with pytest.raises(FullRegenConfirmRequiredError):
            regenerate_full(card_id, confirmed=False, llm=_SectionLlm())
    finally:
        _cleanup(db_connection, event_id, card_id)


def test_full_regen_blocked_at_two_without_po_flag(db_connection) -> None:
    event_id, card_id = _insert_draft_card(db_connection, full_regen_count=2)
    try:
        with pytest.raises(FullRegenBlockedError):
            regenerate_full(card_id, confirmed=True, llm=_SectionLlm())
    finally:
        _cleanup(db_connection, event_id, card_id)


def test_regenerate_section_api_returns_post_checks(db_connection) -> None:
    event_id, card_id = _insert_draft_card(db_connection)
    try:
        client = TestClient(app)
        with patch("app.api.admin_review.regenerate_section") as mock_regen:
            from app.services.card_regen import SectionRegenResult
            from app.services.number_validator import NumberValidationResult

            mock_regen.return_value = SectionRegenResult(
                card_id=card_id,
                section="context",
                previous_hash="aaa",
                new_hash="bbb",
                post_check=type(
                    "Post",
                    (),
                    {
                        "number_validation": NumberValidationResult(status="PASS"),
                        "consistency_check": {"status": "PASS", "conflicts": []},
                    },
                )(),
            )
            response = client.post(
                f"/api/cards/{card_id}/regenerate-section",
                json={"section": "context", "editor_note": "Sharpen causal chain."},
            )
        assert response.status_code == 200
        body = response.json()
        assert body["section"] == "context"
        assert body["number_validation"]["status"] == "PASS"
        assert body["consistency_check"]["status"] == "PASS"
    finally:
        _cleanup(db_connection, event_id, card_id)
