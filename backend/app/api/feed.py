"""Pulse feed API (P1-S9)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.services.feed import build_feed_response

router = APIRouter()


@router.get("/feed")
def get_feed(
    category: str | None = Query(
        default=None,
        description="Comma-separated event categories (e.g. macro,rbi_policy).",
    ),
    horizon: str | None = Query(
        default=None,
        description="Horizon window: under_1y | 1_3y | 3_7y | 7_plus (overrides session profile).",
    ),
    session_id: UUID | None = Query(
        default=None,
        description="Onboarding session id for profile join (horizon default).",
    ),
) -> dict:
    if horizon is not None and horizon not in {
        "under_1y",
        "1_3y",
        "3_7y",
        "7_plus",
    }:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "invalid_horizon", "message": "Unknown horizon value"},
        )
    try:
        return build_feed_response(session_id=session_id, horizon=horizon, category=category)
    except RuntimeError as exc:
        if "SUPABASE_DB_URL" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"code": "db_unavailable", "message": str(exc)},
            ) from exc
        raise
