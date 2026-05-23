"""Mirror stats strip computation (P2-S1)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

AccuracyGrade = Literal["correct", "partial", "incorrect", "monitoring"] | None

ACCURACY_STRONG_THRESHOLD_PCT = 70.0

ACTIVE_LIFECYCLE_STATES: frozenset[str] = frozenset(
    {"active", "signal_triggered", "thesis_confirmed", "thesis_weakened"}
)


@dataclass(frozen=True)
class PredictionGradeSnapshot:
    mechanism_accuracy: AccuracyGrade = None
    business_accuracy: AccuracyGrade = None
    market_accuracy: AccuracyGrade = None
    gap_insight: str | None = None


@dataclass(frozen=True)
class MirrorStatsResult:
    total_predictions: int
    mechanism_accuracy_pct: float | None
    market_accuracy_pct: float | None
    reasoning_gaps_found: int
    mechanism_tone: Literal["strong", "developing", "neutral"]
    market_tone: Literal["strong", "developing", "neutral"]


def accuracy_tone(pct: float | None) -> Literal["strong", "developing", "neutral"]:
    if pct is None:
        return "neutral"
    if pct >= ACCURACY_STRONG_THRESHOLD_PCT:
        return "strong"
    return "developing"


def _graded_values(grades: list[AccuracyGrade]) -> list[str]:
    return [g for g in grades if g in ("correct", "partial", "incorrect")]


def _accuracy_pct(grades: list[AccuracyGrade]) -> float | None:
    graded = _graded_values(grades)
    if not graded:
        return None
    correct = sum(1 for g in graded if g == "correct")
    return round(100.0 * correct / len(graded), 1)


def _count_reasoning_gaps(rows: list[PredictionGradeSnapshot]) -> int:
    gaps = 0
    for row in rows:
        insight = (row.gap_insight or "").strip()
        if insight:
            gaps += 1
            continue
        levels = (row.mechanism_accuracy, row.business_accuracy, row.market_accuracy)
        if any(level in ("incorrect", "partial") for level in levels):
            gaps += 1
    return gaps


def compute(rows: list[PredictionGradeSnapshot]) -> MirrorStatsResult:
    """Pure stats computation for the Mirror strip."""
    total = len(rows)
    mechanism_pct = _accuracy_pct([r.mechanism_accuracy for r in rows])
    market_pct = _accuracy_pct([r.market_accuracy for r in rows])
    return MirrorStatsResult(
        total_predictions=total,
        mechanism_accuracy_pct=mechanism_pct,
        market_accuracy_pct=market_pct,
        reasoning_gaps_found=_count_reasoning_gaps(rows),
        mechanism_tone=accuracy_tone(mechanism_pct),
        market_tone=accuracy_tone(market_pct),
    )


def mirror_filter_status(lifecycle_state: str) -> Literal["resolved", "active", "pending"]:
    if lifecycle_state == "resolved":
        return "resolved"
    if lifecycle_state in ACTIVE_LIFECYCLE_STATES:
        return "active"
    return "pending"


__all__ = [
    "ACCURACY_STRONG_THRESHOLD_PCT",
    "ACTIVE_LIFECYCLE_STATES",
    "MirrorStatsResult",
    "PredictionGradeSnapshot",
    "accuracy_tone",
    "compute",
    "mirror_filter_status",
]
