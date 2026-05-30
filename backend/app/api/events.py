"""Event confidence explainability API (P3-S1g / G-01)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.diagnostics.timing import DbRequestTimer, json_response_with_timing
from app.http.cache_control import PUBLISHED_READ_CACHE
from app.services.confidence_scorer import build_confidence_breakdown_payload

router = APIRouter()

# Per cross-phase perf standards: breakdown cached 60s per event_id.
CONFIDENCE_BREAKDOWN_CACHE = PUBLISHED_READ_CACHE


@router.get("/events/{event_id}/confidence-breakdown")
def get_confidence_breakdown(event_id: UUID) -> JSONResponse:
    with DbRequestTimer() as timer:
        payload = build_confidence_breakdown_payload(event_id)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "event_not_found", "message": "Event not found"},
            )
    return json_response_with_timing(
        payload,
        timer,
        cache_control=CONFIDENCE_BREAKDOWN_CACHE,
    )
