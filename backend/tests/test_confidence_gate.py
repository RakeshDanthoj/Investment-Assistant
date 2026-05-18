"""Confidence gate routing — P1-S11."""

import pytest

from app.services.confidence_gate import route
from app.services.signal_check import SignalEvalResult


def test_gate_high_requires_three_direct_sources() -> None:
    r = SignalEvalResult(
        direct_source_ids=["a", "b", "c"],
        partial_source_ids=[],
    )
    d = route(r)
    assert d.tier == "high"
    assert "three_plus" in d.reason


def test_gate_medium_one_to_two_direct() -> None:
    r = SignalEvalResult(direct_source_ids=["x"], partial_source_ids=["y"])
    d = route(r)
    assert d.tier == "medium"


def test_gate_medium_partial_only_small_band() -> None:
    r = SignalEvalResult(direct_source_ids=[], partial_source_ids=["p1", "p2"])
    d = route(r)
    assert d.tier == "medium"


def test_gate_low_diffuse_partial_field() -> None:
    r = SignalEvalResult(
        direct_source_ids=[],
        partial_source_ids=["a", "b", "c"],
    )
    d = route(r)
    assert d.tier == "low"


def test_gate_rejects_empty_evaluation() -> None:
    with pytest.raises(ValueError):
        route(SignalEvalResult())
