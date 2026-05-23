"""Mirror stats threshold colouring and filter status (P2-S1)."""

from app.services.mirror_stats import (
    ACCURACY_STRONG_THRESHOLD_PCT,
    PredictionGradeSnapshot,
    accuracy_tone,
    compute,
    mirror_filter_status,
)


def test_accuracy_tone_strong_at_threshold() -> None:
    assert accuracy_tone(ACCURACY_STRONG_THRESHOLD_PCT) == "strong"
    assert accuracy_tone(ACCURACY_STRONG_THRESHOLD_PCT + 0.1) == "strong"


def test_accuracy_tone_developing_below_threshold() -> None:
    assert accuracy_tone(ACCURACY_STRONG_THRESHOLD_PCT - 0.1) == "developing"
    assert accuracy_tone(0.0) == "developing"


def test_accuracy_tone_neutral_when_ungraded() -> None:
    assert accuracy_tone(None) == "neutral"


def test_compute_mechanism_and_market_percentages() -> None:
    rows = [
        PredictionGradeSnapshot("correct", "partial", "incorrect"),
        PredictionGradeSnapshot("correct", "correct", "correct"),
        PredictionGradeSnapshot("monitoring", "monitoring", "monitoring"),
    ]
    stats = compute(rows)
    assert stats.total_predictions == 3
    assert stats.mechanism_accuracy_pct == 100.0
    assert stats.market_accuracy_pct == 50.0
    assert stats.mechanism_tone == "strong"
    assert stats.market_tone == "developing"
    assert stats.reasoning_gaps_found == 1


def test_mirror_filter_status_mapping() -> None:
    assert mirror_filter_status("resolved") == "resolved"
    assert mirror_filter_status("active") == "active"
    assert mirror_filter_status("thesis_confirmed") == "active"
    assert mirror_filter_status("published") == "pending"
