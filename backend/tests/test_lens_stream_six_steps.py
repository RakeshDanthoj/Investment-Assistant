"""Lens SSE pipeline emits six PRD-named milestones in order (P2-S7)."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.services.lens_pipeline import run
from app.services.lens_pipeline_steps import LENS_PIPELINE_STEPS
from app.services.lens_queries import LensQueryRow

QUERY_ID = uuid4()
USER_ID = uuid4()
CARD_ID = uuid4()
EVENT_ID = uuid4()


def _row(*, status: str = "queued") -> LensQueryRow:
    return LensQueryRow(
        id=QUERY_ID,
        query="What would a US recession mean for Indian IT exporters?",
        sector="macro",
        horizon="3_7y",
        status=status,  # type: ignore[arg-type]
        card_id=None,
        created_at=datetime(2026, 5, 24, tzinfo=UTC),
    )


def _collect_step_names(events: list[dict]) -> list[str]:
    return [e["name"] for e in events if e.get("event") == "step" and e.get("status") == "done"]


@patch("app.services.lens_pipeline.update_query_status")
@patch("app.services.lens_pipeline.create_lens_event_for_query", return_value=EVENT_ID)
@patch("app.services.lens_pipeline.draft_card_from_event", return_value=CARD_ID)
@patch("app.services.lens_pipeline.get_query_for_user")
def test_run_emits_six_named_steps_in_order(
    mock_get,
    mock_draft,
    _mock_event,
    _mock_status,
) -> None:
    mock_get.return_value = _row()

    def fake_draft(*_args, on_milestone=None, **_kwargs):
        if on_milestone is not None:
            for step in LENS_PIPELINE_STEPS:
                on_milestone(step)
        return CARD_ID

    mock_draft.side_effect = fake_draft

    payloads = list(run(QUERY_ID, user_id=USER_ID))
    done_steps = _collect_step_names(payloads)

    assert done_steps == list(LENS_PIPELINE_STEPS)
    assert payloads[-1] == {"event": "complete", "card_id": str(CARD_ID)}


@patch("app.services.lens_pipeline.get_query_for_user")
def test_run_short_circuits_when_already_done(mock_get) -> None:
    mock_get.return_value = replace(_row(status="done"), card_id=CARD_ID)

    payloads = list(run(QUERY_ID, user_id=USER_ID))

    assert payloads == [{"event": "complete", "card_id": str(CARD_ID)}]
    assert _collect_step_names(payloads) == []


@patch("app.services.lens_pipeline.get_query_for_user")
def test_run_raises_when_query_missing(mock_get) -> None:
    mock_get.return_value = None
    with pytest.raises(LookupError):
        list(run(QUERY_ID, user_id=USER_ID))
