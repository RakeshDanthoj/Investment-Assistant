"""Three-level Mirror prediction grading against Original View (P2-S2)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Protocol

from app.services.llm_client import LlmClient, load_prompt_markdown, render_prompt

PROMPT_GRADING_VERSION = "grading.v1"

ACCURACY_VALUES = frozenset({"correct", "partial", "incorrect", "monitoring"})

_GENERIC_GAP_MARKERS = frozenset(
    {
        "markets are unpredictable",
        "market is unpredictable",
        "only time will tell",
        "time will tell",
        "it remains to be seen",
        "could go either way",
        "uncertainty remains high",
        "hard to predict",
        "impossible to predict",
    }
)


class SupportsGradingCompletion(Protocol):
    def complete_json(
        self,
        *,
        system: str,
        user: str,
        prompt_version: str,
        max_tokens: int = 4096,
    ) -> tuple[dict[str, Any], dict[str, int]]: ...


class GradingQualityError(ValueError):
    """LLM grading output failed validation."""


@dataclass(frozen=True)
class GradeResult:
    mechanism_accuracy: str
    business_accuracy: str
    market_accuracy: str
    gap_insight: str


def _assert_accuracy_field(name: str, value: object) -> str:
    if not isinstance(value, str):
        raise GradingQualityError(f"{name} must be a string")
    v = value.strip().lower()
    if v not in ACCURACY_VALUES:
        raise GradingQualityError(f"{name} invalid: {value!r}")
    return v


def parse_grade_payload(data: dict[str, Any]) -> GradeResult:
    mechanism = _assert_accuracy_field("mechanism_accuracy", data.get("mechanism_accuracy"))
    business = _assert_accuracy_field("business_accuracy", data.get("business_accuracy"))
    market = _assert_accuracy_field("market_accuracy", data.get("market_accuracy"))
    gap = data.get("gap_insight")
    if not isinstance(gap, str) or len(gap.strip()) < 24:
        raise GradingQualityError("gap_insight too short or missing")
    gap_clean = gap.strip()
    low = gap_clean.lower()
    if any(marker in low for marker in _GENERIC_GAP_MARKERS):
        raise GradingQualityError("gap_insight uses forbidden generic phrasing")
    return GradeResult(
        mechanism_accuracy=mechanism,
        business_accuracy=business,
        market_accuracy=market,
        gap_insight=gap_clean,
    )


def _ice_snapshot(original_publish: dict[str, Any]) -> dict[str, Any]:
    snap = original_publish.get("ice_snapshot")
    if isinstance(snap, dict):
        return snap
    return {}


def _final_card_view(final_card: dict[str, Any]) -> dict[str, Any]:
    ev = final_card.get("evidence_layer")
    if isinstance(ev, str):
        try:
            ev = json.loads(ev) if ev.strip() else {}
        except json.JSONDecodeError:
            ev = {}
    if not isinstance(ev, dict):
        ev = {}
    return {
        "title": final_card.get("title") or final_card.get("card_title"),
        "insight_layer": final_card.get("insight_layer"),
        "context_layer": final_card.get("context_layer"),
        "evidence_layer": ev,
        "dissenting_view": final_card.get("dissenting_view"),
        "framework_behind_this": final_card.get("framework_behind_this"),
        "lifecycle_state": final_card.get("lifecycle_state"),
        "event_title": final_card.get("event_title"),
        "event_category": final_card.get("event_category"),
    }


def build_grading_user_payload(
    *,
    prediction_text: str,
    original_publish: dict[str, Any],
    final_card: dict[str, Any],
) -> str:
    """Structured user message for the grader (Original View vs Final)."""
    original_ice = _ice_snapshot(original_publish)
    payload = {
        "user_prediction": prediction_text.strip(),
        "original_view": original_ice,
        "original_publish_meta": {
            "card_title": original_publish.get("card_title"),
            "event_category": original_publish.get("event_category"),
            "kind": original_publish.get("kind"),
        },
        "final_card_state": _final_card_view(final_card),
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def grade(
    *,
    prediction_text: str,
    original_publish: dict[str, Any],
    final_card: dict[str, Any],
    llm: SupportsGradingCompletion | None = None,
) -> GradeResult:
    """
    Grade one prediction. ``original_publish`` must be the Day-1 ``initial_publish``
    track_record payload; ``final_card`` is the live card at resolution.
    """
    template = load_prompt_markdown("grading.v1.md")
    user_blob = build_grading_user_payload(
        prediction_text=prediction_text,
        original_publish=original_publish,
        final_card=final_card,
    )
    system = (
        "You grade investor learning predictions for FinnWise Mirror. "
        "Respond with JSON only, matching the schema in the prompt."
    )
    model = llm or LlmClient()
    raw, _usage = model.complete_json(
        system=system,
        user=render_prompt(template, {"grading_payload": user_blob}),
        prompt_version=PROMPT_GRADING_VERSION,
        max_tokens=1024,
    )
    return parse_grade_payload(raw)


__all__ = [
    "ACCURACY_VALUES",
    "GradeResult",
    "GradingQualityError",
    "PROMPT_GRADING_VERSION",
    "build_grading_user_payload",
    "grade",
    "parse_grade_payload",
]
