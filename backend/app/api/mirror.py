"""The Mirror — prediction history and stats (P2-S1)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.api.mirror_notifications import router as mirror_notifications_router
from app.core.auth import CurrentUser
from app.services.mirror_predictions import (
    MirrorPredictionRow,
    list_predictions,
    stats_for_user,
)
from app.services.mirror_stats import MirrorStatsResult

router = APIRouter(prefix="/mirror", tags=["mirror"])
router.include_router(mirror_notifications_router)

MirrorStatusQuery = Literal["resolved", "active", "pending"] | None


class MirrorPredictionItem(BaseModel):
    id: UUID
    card_id: UUID
    prediction_text: str
    logged_at: datetime
    mechanism_accuracy: str | None = None
    business_accuracy: str | None = None
    market_accuracy: str | None = None
    gap_insight: str | None = None
    card_title: str
    event_title: str
    event_category: str
    lifecycle_state: str
    mirror_status: Literal["resolved", "active", "pending"]
    linked_map_module_id: str | None = None
    linked_map_module_name: str | None = None


class MirrorPredictionsResponse(BaseModel):
    items: list[MirrorPredictionItem]
    limit: int
    offset: int


class MirrorStatsResponse(BaseModel):
    total_predictions: int
    mechanism_accuracy_pct: float | None
    market_accuracy_pct: float | None
    reasoning_gaps_found: int
    mechanism_tone: Literal["strong", "developing", "neutral"]
    market_tone: Literal["strong", "developing", "neutral"]


def _row_to_item(row: MirrorPredictionRow) -> MirrorPredictionItem:
    return MirrorPredictionItem(
        id=row.id,
        card_id=row.card_id,
        prediction_text=row.prediction_text,
        logged_at=row.logged_at,
        mechanism_accuracy=row.mechanism_accuracy,
        business_accuracy=row.business_accuracy,
        market_accuracy=row.market_accuracy,
        gap_insight=row.gap_insight,
        card_title=row.card_title,
        event_title=row.event_title,
        event_category=row.event_category,
        lifecycle_state=row.lifecycle_state,
        mirror_status=row.mirror_status,
        linked_map_module_id=row.linked_map_module_id,
        linked_map_module_name=row.linked_map_module_name,
    )


def _stats_to_response(stats: MirrorStatsResult) -> MirrorStatsResponse:
    return MirrorStatsResponse(
        total_predictions=stats.total_predictions,
        mechanism_accuracy_pct=stats.mechanism_accuracy_pct,
        market_accuracy_pct=stats.market_accuracy_pct,
        reasoning_gaps_found=stats.reasoning_gaps_found,
        mechanism_tone=stats.mechanism_tone,
        market_tone=stats.market_tone,
    )


def _db_unavailable(exc: RuntimeError) -> None:
    if "SUPABASE_DB_URL" in str(exc):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "db_unavailable", "message": str(exc)},
        ) from exc
    raise exc


@router.get("/predictions", response_model=MirrorPredictionsResponse)
def get_mirror_predictions(
    current_user: CurrentUser,
    status_filter: MirrorStatusQuery = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> MirrorPredictionsResponse:
    try:
        rows = list_predictions(
            UUID(current_user.id),
            status=status_filter,
            limit=limit,
            offset=offset,
        )
    except RuntimeError as exc:
        _db_unavailable(exc)
    return MirrorPredictionsResponse(
        items=[_row_to_item(row) for row in rows],
        limit=limit,
        offset=offset,
    )


@router.get("/stats", response_model=MirrorStatsResponse)
def get_mirror_stats(current_user: CurrentUser) -> MirrorStatsResponse:
    try:
        stats = stats_for_user(UUID(current_user.id))
    except RuntimeError as exc:
        _db_unavailable(exc)
    return _stats_to_response(stats)
