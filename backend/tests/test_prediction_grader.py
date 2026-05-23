"""Unit tests for Mirror prediction grader (P2-S2)."""

import json

import pytest

from app.services.prediction_grader import (
    GradingQualityError,
    build_grading_user_payload,
    grade,
    parse_grade_payload,
)


class _FakeGraderLlm:
    def __init__(self, payload: dict) -> None:
        self._payload = payload
        self.last_user: str | None = None

    def complete_json(self, *, system: str, user: str, prompt_version: str, max_tokens: int = 4096):
        del system, prompt_version, max_tokens
        self.last_user = user
        return dict(self._payload), {"input_tokens": 1, "output_tokens": 1}


def test_parse_grade_payload_accepts_valid() -> None:
    result = parse_grade_payload(
        {
            "mechanism_accuracy": "correct",
            "business_accuracy": "partial",
            "market_accuracy": "incorrect",
            "gap_insight": (
                "You focused on liquidity stress while the card's mechanism was "
                "a repricing of duration risk through the bond channel."
            ),
        }
    )
    assert result.mechanism_accuracy == "correct"
    assert result.business_accuracy == "partial"
    assert result.market_accuracy == "incorrect"


def test_parse_grade_payload_rejects_generic_gap() -> None:
    with pytest.raises(GradingQualityError, match="generic"):
        parse_grade_payload(
            {
                "mechanism_accuracy": "incorrect",
                "business_accuracy": "incorrect",
                "market_accuracy": "incorrect",
                "gap_insight": "Markets are unpredictable so any call is hard.",
            }
        )


def test_grade_uses_llm_and_validates_output() -> None:
    original = {
        "kind": "initial_publish",
        "card_title": "RBI holds rates",
        "ice_snapshot": {
            "title": "ORIGINAL_INSIGHT_MARKER",
            "insight_layer": "Original mechanism: liquidity channel [MEASURED]",
            "context_layer": "Original context [MEASURED]",
        },
    }
    final = {
        "title": "FINAL_TITLE_ONLY",
        "insight_layer": "Final mechanism: duration channel [MEASURED]",
        "context_layer": "Final context [MEASURED]",
        "evidence_layer": {},
        "lifecycle_state": "resolved",
    }
    fake = _FakeGraderLlm(
        {
            "mechanism_accuracy": "partial",
            "business_accuracy": "correct",
            "market_accuracy": "monitoring",
            "gap_insight": (
                "You named liquidity first while the resolved card shows duration "
                "repricing as the dominant transmission path."
            ),
        }
    )
    result = grade(
        prediction_text="Liquidity will tighten before earnings react.",
        original_publish=original,
        final_card=final,
        llm=fake,
    )
    assert result.mechanism_accuracy == "partial"
    assert fake.last_user is not None
    assert "ORIGINAL_INSIGHT_MARKER" in fake.last_user
    assert "ORIGINAL_INSIGHT_MARKER" in build_grading_user_payload(
        prediction_text="x",
        original_publish=original,
        final_card=final,
    )


def test_build_grading_payload_includes_original_ice_not_only_final_title() -> None:
    blob = build_grading_user_payload(
        prediction_text="Test prediction text here.",
        original_publish={
            "kind": "initial_publish",
            "ice_snapshot": {"insight_layer": "DAY_ONE_ONLY_INSIGHT"},
        },
        final_card={"title": "Live title", "insight_layer": "LIVE_INSIGHT"},
    )
    data = json.loads(blob)
    assert data["original_view"]["insight_layer"] == "DAY_ONE_ONLY_INSIGHT"
    assert data["final_card_state"]["insight_layer"] == "LIVE_INSIGHT"
