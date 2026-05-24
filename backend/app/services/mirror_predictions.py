"""Mirror prediction list queries joined with card metadata (P2-S1)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from psycopg.rows import dict_row

from app.db.connection import connection
from app.services.mirror_stats import (
    MirrorStatsResult,
    PredictionGradeSnapshot,
    compute,
    mirror_filter_status,
)
from app.services.reasoning_gap_detector import infer_gap_type_for_prediction
from app.services.reasoning_gap_map import resolve_module_for_gap_type

MirrorStatusFilter = Literal["resolved", "active", "pending"] | None

_DEFAULT_LIMIT = 50
_MAX_LIMIT = 100


@dataclass(frozen=True)
class MirrorPredictionRow:
    id: UUID
    card_id: UUID
    prediction_text: str
    logged_at: datetime
    mechanism_accuracy: str | None
    business_accuracy: str | None
    market_accuracy: str | None
    gap_insight: str | None
    card_title: str
    event_title: str
    event_category: str
    lifecycle_state: str
    mirror_status: Literal["resolved", "active", "pending"]
    linked_map_module_id: str | None
    linked_map_module_name: str | None


def _linked_map_fields(
    *,
    mechanism_accuracy: str | None,
    business_accuracy: str | None,
    market_accuracy: str | None,
) -> tuple[str | None, str | None]:
    gap_type = infer_gap_type_for_prediction(
        mechanism_accuracy,
        business_accuracy,
        market_accuracy,
    )
    if gap_type is None:
        return None, None
    module = resolve_module_for_gap_type(gap_type)
    if module is None:
        return None, None
    return str(module.id), module.title


def _parse_ts(value: object) -> datetime | None:
    if not isinstance(value, datetime):
        return None
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _list_sql(*, status: MirrorStatusFilter) -> str:
    base = """
    SELECT
      up.id,
      up.card_id,
      up.prediction_text,
      up.logged_at,
      up.mechanism_accuracy,
      up.business_accuracy,
      up.market_accuracy,
      up.gap_insight,
      c.title AS card_title,
      c.lifecycle_state::text AS lifecycle_state,
      e.title AS event_title,
      e.category::text AS event_category
    FROM public.user_predictions up
    INNER JOIN public.cards c ON c.id = up.card_id
    INNER JOIN public.events e ON e.id = c.event_id
    WHERE up.user_id = %s::uuid
    """

    if status == "resolved":
        base += " AND c.lifecycle_state::text = 'resolved'"
    elif status == "active":
        base += """
          AND c.lifecycle_state::text = ANY(
            ARRAY['active','signal_triggered','thesis_confirmed','thesis_weakened']::text[]
          )
        """
    elif status == "pending":
        base += """
          AND c.lifecycle_state::text NOT IN (
            'resolved','active','signal_triggered','thesis_confirmed','thesis_weakened'
          )
        """

    base += " ORDER BY up.logged_at DESC LIMIT %s OFFSET %s"
    return base


def list_predictions(
    user_id: UUID,
    *,
    status: MirrorStatusFilter = None,
    limit: int = _DEFAULT_LIMIT,
    offset: int = 0,
) -> list[MirrorPredictionRow]:
    lim = max(1, min(limit, _MAX_LIMIT))
    off = max(0, offset)
    stmt = _list_sql(status=status)
    params: list[object] = [str(user_id), lim, off]

    rows: list[MirrorPredictionRow] = []
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, params)
        for row in cur.fetchall():
            logged_at = _parse_ts(row["logged_at"])
            if logged_at is None:
                continue
            lifecycle = str(row["lifecycle_state"])
            mech = row.get("mechanism_accuracy")
            biz = row.get("business_accuracy")
            market = row.get("market_accuracy")
            module_id, module_name = _linked_map_fields(
                mechanism_accuracy=mech,
                business_accuracy=biz,
                market_accuracy=market,
            )
            rows.append(
                MirrorPredictionRow(
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
            )
    return rows


def stats_for_user(user_id: UUID) -> MirrorStatsResult:
    stmt = """
    SELECT
      up.mechanism_accuracy,
      up.business_accuracy,
      up.market_accuracy,
      up.gap_insight
    FROM public.user_predictions up
    WHERE up.user_id = %s::uuid
    """
    snapshots: list[PredictionGradeSnapshot] = []
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, (str(user_id),))
        for row in cur.fetchall():
            snapshots.append(
                PredictionGradeSnapshot(
                    mechanism_accuracy=row.get("mechanism_accuracy"),
                    business_accuracy=row.get("business_accuracy"),
                    market_accuracy=row.get("market_accuracy"),
                    gap_insight=row.get("gap_insight"),
                )
            )
    return compute(snapshots)


__all__ = [
    "MirrorPredictionRow",
    "MirrorStatusFilter",
    "list_predictions",
    "stats_for_user",
]
