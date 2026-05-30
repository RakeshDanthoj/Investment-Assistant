"""Confidence gate routing from effective scores — P3-S1g."""

from app.core.confidence_config import THRESHOLDS
from app.services.confidence_gate import route


def test_gate_high_at_threshold() -> None:
    d = route(THRESHOLDS["high"])
    assert d.tier == "high"
    assert d.reason == "score_gte_075"


def test_gate_medium_narrow_band() -> None:
    d = route(0.60)
    assert d.tier == "medium"
    assert d.reason == "score_055_074"


def test_gate_low_below_medium() -> None:
    d = route(THRESHOLDS["medium_low"] - 0.01)
    assert d.tier == "low"
    assert d.reason == "score_lt_055"


def test_gate_boundary_medium_low() -> None:
    assert route(THRESHOLDS["medium_low"]).tier == "medium"

