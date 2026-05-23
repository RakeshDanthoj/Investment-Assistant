"""Card detail for The Thread — Current vs Original (immutable publish snapshot)."""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.diagnostics.timing import DbRequestTimer, json_response_with_timing, timing_headers
from app.services.card_detail import build_card_detail

router = APIRouter()


@router.get("/{card_id}")
def get_card_detail(
    card_id: UUID,
    view: Literal["current", "original"] = Query(
        default="current",
        description="current = live card; original = Day-1 track_record snapshot.",
    ),
) -> JSONResponse:
    with DbRequestTimer() as timer:
        try:
            payload = build_card_detail(card_id, view=view)
        except RuntimeError as exc:
            if "SUPABASE_DB_URL" in str(exc):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail={"code": "db_unavailable", "message": str(exc)},
                ) from exc
            raise
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": "card_not_found"
                    if view == "current"
                    else "original_view_unavailable",
                    "message": "Card not found"
                    if view == "current"
                    else "Original view exists after publish — no snapshot yet.",
                },
                headers=timing_headers(timer.snapshot()),
            )
    return json_response_with_timing(payload, timer)
