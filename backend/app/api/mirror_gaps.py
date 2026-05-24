"""The Mirror — reasoning-gap analysis (P2-S4)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.auth import CurrentUser
from app.services.reasoning_gap_detector import ReasoningGap, analyse_with_meta

router = APIRouter(prefix="/mirror", tags=["mirror"])


class ReasoningGapItem(BaseModel):
    gap_type: str
    gap_name: str
    pattern_explanation: str
    linked_map_module_id: str
    linked_map_module_name: str


class MirrorGapsResponse(BaseModel):
    items: list[ReasoningGapItem]
    insufficient_history: bool


def _gap_to_item(gap: ReasoningGap) -> ReasoningGapItem:
    return ReasoningGapItem(
        gap_type=gap.gap_type,
        gap_name=gap.gap_name,
        pattern_explanation=gap.pattern_explanation,
        linked_map_module_id=str(gap.linked_map_module_id),
        linked_map_module_name=gap.linked_map_module_name,
    )


def _db_unavailable(exc: RuntimeError) -> None:
    if "SUPABASE_DB_URL" in str(exc):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "db_unavailable", "message": str(exc)},
        ) from exc
    raise exc


def _build_response(user_id: UUID) -> MirrorGapsResponse:
    try:
        gaps, insufficient = analyse_with_meta(user_id)
    except RuntimeError as exc:
        _db_unavailable(exc)
    return MirrorGapsResponse(
        items=[_gap_to_item(g) for g in gaps],
        insufficient_history=insufficient,
    )


@router.get("/gaps", response_model=MirrorGapsResponse)
def get_mirror_gaps(current_user: CurrentUser) -> MirrorGapsResponse:
    """Top-3 reasoning gaps derived from graded prediction history."""
    return _build_response(UUID(current_user.id))


@router.post("/gaps/refresh", response_model=MirrorGapsResponse)
def refresh_mirror_gaps(current_user: CurrentUser) -> MirrorGapsResponse:
    """Re-run gap analysis on demand (PRD Refresh analysis)."""
    return _build_response(UUID(current_user.id))
