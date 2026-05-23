"""The Mirror — streak tracker grid (P2-S5)."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.auth import CurrentUser
from app.services.mirror_streak import (
    MirrorStreakResult,
    StreakCell,
    streak_for_user,
)

router = APIRouter(prefix="/mirror", tags=["mirror"])


class StreakCellResponse(BaseModel):
    letter: Literal["M", "P", "✗", "·", "–"]
    grade: Literal["correct", "partial", "incorrect", "monitoring", "empty"]


class MirrorStreakResponse(BaseModel):
    cells: list[StreakCellResponse]
    mechanism_accuracy_pct: float | None
    market_accuracy_pct: float | None
    summary: str


def _cell_to_response(cell: StreakCell) -> StreakCellResponse:
    return StreakCellResponse(letter=cell.letter, grade=cell.grade)


def _result_to_response(result: MirrorStreakResult) -> MirrorStreakResponse:
    return MirrorStreakResponse(
        cells=[_cell_to_response(c) for c in result.cells],
        mechanism_accuracy_pct=result.mechanism_accuracy_pct,
        market_accuracy_pct=result.market_accuracy_pct,
        summary=result.summary,
    )


def _db_unavailable(exc: RuntimeError) -> None:
    if "SUPABASE_DB_URL" in str(exc):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "db_unavailable", "message": str(exc)},
        ) from exc
    raise exc


@router.get("/streak", response_model=MirrorStreakResponse)
def get_mirror_streak(current_user: CurrentUser) -> MirrorStreakResponse:
    try:
        result = streak_for_user(UUID(current_user.id))
    except RuntimeError as exc:
        _db_unavailable(exc)
    return _result_to_response(result)
