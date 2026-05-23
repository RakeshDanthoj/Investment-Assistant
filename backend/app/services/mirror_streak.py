"""Mirror streak grid — last 14 mechanism grades (P2-S5)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from psycopg.rows import dict_row

from app.db.connection import connection
from app.services.mirror_stats import (
    PredictionGradeSnapshot,
    compute,
)

STREAK_SLOT_COUNT = 14

StreakGrade = Literal["correct", "partial", "incorrect", "monitoring", "empty"]
StreakLetter = Literal["M", "P", "✗", "·", "–"]


@dataclass(frozen=True)
class StreakCell:
    letter: StreakLetter
    grade: StreakGrade


@dataclass(frozen=True)
class MirrorStreakResult:
    cells: list[StreakCell]
    mechanism_accuracy_pct: float | None
    market_accuracy_pct: float | None
    summary: str


def cell_from_mechanism_grade(grade: str | None) -> StreakCell:
    """Map mechanism_accuracy to PRD §5 Screen 4 streak cell."""
    if grade == "correct":
        return StreakCell(letter="M", grade="correct")
    if grade == "partial":
        return StreakCell(letter="P", grade="partial")
    if grade == "incorrect":
        return StreakCell(letter="✗", grade="incorrect")
    if grade == "monitoring":
        return StreakCell(letter="·", grade="monitoring")
    return StreakCell(letter="·", grade="monitoring")


def build_streak_cells(mechanism_grades: list[str | None]) -> list[StreakCell]:
    """Most recent first; pad with transparent empty slots to 14."""
    cells = [cell_from_mechanism_grade(g) for g in mechanism_grades[:STREAK_SLOT_COUNT]]
    while len(cells) < STREAK_SLOT_COUNT:
        cells.append(StreakCell(letter="–", grade="empty"))
    return cells


def format_pct(pct: float | None) -> str:
    if pct is None:
        return "—"
    rounded = round(pct, 1)
    if rounded == int(rounded):
        return f"{int(rounded)}%"
    return f"{rounded}%"


def build_streak_summary(
    mechanism_pct: float | None,
    market_pct: float | None,
) -> str:
    """Plain-English comparison of mechanism vs market reaction accuracy."""
    mech_label = format_pct(mechanism_pct)
    market_label = format_pct(market_pct)

    if mechanism_pct is None and market_pct is None:
        return (
            "Log predictions on Thread cards and wait for them to resolve. "
            "Your streak grid will fill in as grades arrive — the summary compares "
            "how often your causal reasoning matched outcomes versus how often "
            "market prices moved the way you expected."
        )

    if mechanism_pct is None:
        return (
            f"Your market reaction match is {market_label} across graded predictions. "
            "Mechanism scores will appear once cards resolve and grading completes."
        )

    if market_pct is None:
        return (
            f"Your mechanism accuracy is {mech_label} so far. "
            "Market reaction scores appear once enough resolved cards have been graded."
        )

    gap = (mechanism_pct or 0) - (market_pct or 0)

    if gap >= 15:
        return (
            f"Your mechanism accuracy ({mech_label}) is ahead of market reaction match "
            f"({market_label}). That gap is normal — and common for early investors. "
            "Sound causal reasoning often shows up in fundamentals before prices fully "
            "reflect it; markets can lag or overshoot for weeks. The streak grid makes "
            "that split visible so you practise mechanism discipline without treating "
            "every price miss as a reasoning failure."
        )

    if gap <= -15:
        return (
            f"Your market reaction match ({market_label}) is ahead of mechanism accuracy "
            f"({mech_label}). Prices sometimes move for reasons outside your stated "
            "mechanism — liquidity, positioning, or unrelated macro shocks. Use the grid "
            "to check whether your causal chain still held even when the tape disagreed."
        )

    return (
        f"Your mechanism accuracy ({mech_label}) and market reaction match ({market_label}) "
        "are tracking close together. When they diverge — usually with stronger mechanism "
        "than market scores — it is a normal learning pattern: getting the causal chain "
        "right is a separate skill from timing how prices react."
    )


def streak_for_user(user_id: UUID) -> MirrorStreakResult:
    recent_stmt = """
    SELECT up.mechanism_accuracy
    FROM public.user_predictions up
    WHERE up.user_id = %s::uuid
    ORDER BY up.logged_at DESC
    LIMIT %s
    """
    all_stmt = """
    SELECT
      up.mechanism_accuracy,
      up.business_accuracy,
      up.market_accuracy,
      up.gap_insight
    FROM public.user_predictions up
    WHERE up.user_id = %s::uuid
    """

    mechanism_recent: list[str | None] = []
    snapshots: list[PredictionGradeSnapshot] = []

    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(recent_stmt, (str(user_id), STREAK_SLOT_COUNT))
        for row in cur.fetchall():
            mechanism_recent.append(row.get("mechanism_accuracy"))

        cur.execute(all_stmt, (str(user_id),))
        for row in cur.fetchall():
            snapshots.append(
                PredictionGradeSnapshot(
                    mechanism_accuracy=row.get("mechanism_accuracy"),
                    business_accuracy=row.get("business_accuracy"),
                    market_accuracy=row.get("market_accuracy"),
                    gap_insight=row.get("gap_insight"),
                )
            )

    stats = compute(snapshots)
    return MirrorStreakResult(
        cells=build_streak_cells(mechanism_recent),
        mechanism_accuracy_pct=stats.mechanism_accuracy_pct,
        market_accuracy_pct=stats.market_accuracy_pct,
        summary=build_streak_summary(
            stats.mechanism_accuracy_pct,
            stats.market_accuracy_pct,
        ),
    )


__all__ = [
    "STREAK_SLOT_COUNT",
    "MirrorStreakResult",
    "StreakCell",
    "StreakGrade",
    "StreakLetter",
    "build_streak_cells",
    "build_streak_summary",
    "cell_from_mechanism_grade",
    "streak_for_user",
]
