"""Mirror dashboard — single-connection read bundle (PI-S2)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal
from uuid import UUID

from psycopg.rows import dict_row

from app.db.connection import connection
from app.services.mirror_predictions import (
    MirrorPredictionRow,
    MirrorStatusFilter,
    _linked_map_fields,
    _parse_ts,
)
from app.services.mirror_stats import (
    MirrorStatsResult,
    PredictionGradeSnapshot,
    compute,
    mirror_filter_status,
)
from app.services.mirror_streak import (
    MirrorStreakResult,
    build_streak_cells,
    build_streak_summary,
)
from app.services.notify_on_grade import list_unread_card_graded
from app.services.reasoning_gap_detector import (
    MIN_GRADED_RESOLVED,
    GradedPredictionRow,
    ReasoningGap,
    analyse_from_history,
)

_DEFAULT_LIMIT = 50
_MAX_LIMIT = 100

_PREDICTIONS_SQL = """
SELECT
  id,
  card_id,
  prediction_text,
  logged_at,
  mechanism_accuracy,
  business_accuracy,
  market_accuracy,
  gap_insight,
  card_title,
  lifecycle_state,
  event_title,
  event_category
FROM public.mirror_user_predictions_v
WHERE user_id = %s::uuid
ORDER BY logged_at DESC
"""

_GRADED_HISTORY_SQL = """
SELECT
  mechanism_accuracy,
  business_accuracy,
  market_accuracy,
  sector_slug
FROM public.mirror_graded_history_v
WHERE user_id = %s::uuid
ORDER BY history_rank ASC
"""


@dataclass(frozen=True)
class MirrorDashboardBundle:
    stats: MirrorStatsResult
    predictions: list[MirrorPredictionRow]
    limit: int
    offset: int
    streak: MirrorStreakResult
    gaps: list[ReasoningGap]
    insufficient_gaps_history: bool
    unread_notification_rows: list[dict[str, Any]]


def _row_to_prediction(row: dict[str, Any]) -> MirrorPredictionRow | None:
    logged_at = _parse_ts(row.get("logged_at"))
    if logged_at is None:
        return None
    lifecycle = str(row["lifecycle_state"])
    mech = row.get("mechanism_accuracy")
    biz = row.get("business_accuracy")
    market = row.get("market_accuracy")
    module_id, module_name = _linked_map_fields(
        mechanism_accuracy=mech,
        business_accuracy=biz,
        market_accuracy=market,
    )
    return MirrorPredictionRow(
        id=UUID(str(row["id"])),
        card_id=UUID(str(row["card_id"])),
        prediction_text=str(row["prediction_text"]),
        logged_at=logged_at,
        mechanism_accuracy=mech,
        business_accuracy=biz,
        market_accuracy=market,
        gap_insight=row.get("gap_insight"),
        card_title=str(row["card_title"]),
        event_title=str(row["event_title"]),
        event_category=str(row["event_category"]),
        lifecycle_state=lifecycle,
        mirror_status=mirror_filter_status(lifecycle),
        linked_map_module_id=module_id,
        linked_map_module_name=module_name,
    )


def _matches_status(
    mirror_status: Literal["resolved", "active", "pending"],
    status: MirrorStatusFilter,
) -> bool:
    if status is None:
        return True
    return mirror_status == status


def _fetch_predictions_bundle(
    cur,
    user_id: UUID,
    *,
    status: MirrorStatusFilter,
    limit: int,
    offset: int,
) -> tuple[list[MirrorPredictionRow], list[PredictionGradeSnapshot], list[str | None]]:
    cur.execute(_PREDICTIONS_SQL, (str(user_id),))
    all_rows: list[MirrorPredictionRow] = []
    snapshots: list[PredictionGradeSnapshot] = []
    mechanism_recent: list[str | None] = []

    for raw in cur.fetchall():
        row = _row_to_prediction(raw)
        if row is None:
            continue
        snapshots.append(
            PredictionGradeSnapshot(
                mechanism_accuracy=row.mechanism_accuracy,
                business_accuracy=row.business_accuracy,
                market_accuracy=row.market_accuracy,
                gap_insight=row.gap_insight,
            )
        )
        if len(mechanism_recent) < 14:
            mechanism_recent.append(row.mechanism_accuracy)
        if _matches_status(row.mirror_status, status):
            all_rows.append(row)

    lim = max(1, min(limit, _MAX_LIMIT))
    off = max(0, offset)
    page = all_rows[off : off + lim]
    return page, snapshots, mechanism_recent


def _fetch_graded_history(cur, user_id: UUID) -> list[GradedPredictionRow]:
    cur.execute(_GRADED_HISTORY_SQL, (str(user_id),))
    return [
        GradedPredictionRow(
            mechanism_accuracy=row.get("mechanism_accuracy"),
            business_accuracy=row.get("business_accuracy"),
            market_accuracy=row.get("market_accuracy"),
            sector_slug=row.get("sector_slug"),
        )
        for row in cur.fetchall()
    ]


def build_mirror_dashboard(
    user_id: UUID,
    *,
    status: MirrorStatusFilter = None,
    limit: int = _DEFAULT_LIMIT,
    offset: int = 0,
) -> MirrorDashboardBundle:
    """Single pool checkout for Mirror dashboard SSR (PI-S2)."""
    lim = max(1, min(limit, _MAX_LIMIT))
    off = max(0, offset)

    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        predictions, snapshots, mechanism_recent = _fetch_predictions_bundle(
            cur,
            user_id,
            status=status,
            limit=lim,
            offset=off,
        )
        graded_history = _fetch_graded_history(cur, user_id)
        unread_rows = list_unread_card_graded(cur, str(user_id))

    stats = compute(snapshots)
    streak = MirrorStreakResult(
        cells=build_streak_cells(mechanism_recent),
        mechanism_accuracy_pct=stats.mechanism_accuracy_pct,
        market_accuracy_pct=stats.market_accuracy_pct,
        summary=build_streak_summary(
            stats.mechanism_accuracy_pct,
            stats.market_accuracy_pct,
        ),
    )
    insufficient = len(graded_history) < MIN_GRADED_RESOLVED
    gaps = analyse_from_history(graded_history)

    return MirrorDashboardBundle(
        stats=stats,
        predictions=predictions,
        limit=lim,
        offset=off,
        streak=streak,
        gaps=gaps,
        insufficient_gaps_history=insufficient,
        unread_notification_rows=unread_rows,
    )


__all__ = ["MirrorDashboardBundle", "build_mirror_dashboard"]
