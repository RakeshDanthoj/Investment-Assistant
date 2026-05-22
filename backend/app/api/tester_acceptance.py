"""Tester briefing acceptance API (P1-S14)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from app.core.auth import CurrentUser
from app.services.tester_acceptance import (
    TesterAcceptanceError,
    has_accepted,
    record_acceptance,
)

router = APIRouter()


class TesterAcceptResponse(BaseModel):
    ok: bool = True
    accepted_at: datetime


class TesterStatusResponse(BaseModel):
    accepted: bool
    accepted_at: datetime | None = None


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip() or None
    if request.client:
        return request.client.host
    return None


@router.get("/tester/status", response_model=TesterStatusResponse)
def get_tester_status(user: CurrentUser) -> TesterStatusResponse:
    if not has_accepted(user.id):
        return TesterStatusResponse(accepted=False)
    return TesterStatusResponse(accepted=True)


@router.post("/tester/accept", response_model=TesterAcceptResponse)
def accept_tester_briefing(request: Request, user: CurrentUser) -> TesterAcceptResponse:
    if has_accepted(user.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "already_accepted", "message": "Briefing already accepted"},
        )
    try:
        accepted_at = record_acceptance(user_id=user.id, ip=_client_ip(request))
    except TesterAcceptanceError as exc:
        code = str(exc)
        if code == "already_accepted":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": code, "message": "Briefing already accepted"},
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": code, "message": "Could not record acceptance"},
        ) from exc
    return TesterAcceptResponse(accepted_at=accepted_at)


async def require_tester_acceptance(user: CurrentUser) -> None:
    """FastAPI dependency — blocks invited users who have not accepted the briefing."""
    if not has_accepted(user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "tester_acceptance_required",
                "message": "Accept the Phase 1 tester briefing before using this feature",
            },
        )
