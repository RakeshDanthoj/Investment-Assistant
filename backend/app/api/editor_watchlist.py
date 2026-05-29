"""Editorial slow-burn watchlist API (P3-S1e / G-05)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.admin_metrics import require_admin
from app.core.auth import User
from app.services import watchlist as watchlist_svc

router = APIRouter(prefix="/editor", tags=["editor-watchlist"])

WatchlistStatus = Literal["watching", "escalated", "closed"]


class WatchlistItem(BaseModel):
    id: UUID
    event_description: str
    category: str
    added_at: datetime
    review_frequency: str
    last_reviewed_at: datetime | None = None
    escalation_trigger: str | None = None
    status: WatchlistStatus
    escalated_event_id: UUID | None = None


class WatchlistPatchBody(BaseModel):
    status: WatchlistStatus


class EscalateResponse(BaseModel):
    item: WatchlistItem
    event_id: UUID


@router.get("/watchlist", response_model=list[WatchlistItem])
def list_watchlist(
    status: WatchlistStatus | None = None,
    limit: int = 100,
    _: User = Depends(require_admin),
) -> list[WatchlistItem]:
    rows = watchlist_svc.list_watchlist_items(status=status, limit=limit)
    return [WatchlistItem.model_validate(row) for row in rows]


@router.patch("/watchlist/{item_id}", response_model=WatchlistItem)
def patch_watchlist(
    item_id: UUID,
    body: WatchlistPatchBody,
    _: User = Depends(require_admin),
) -> WatchlistItem:
    row = watchlist_svc.patch_watchlist_status(item_id, status=body.status)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist item not found",
        )
    return WatchlistItem.model_validate(row)


@router.post("/watchlist/{item_id}/escalate", response_model=EscalateResponse)
def escalate_watchlist(
    item_id: UUID,
    _: User = Depends(require_admin),
) -> EscalateResponse:
    try:
        item, event_id = watchlist_svc.escalate_watchlist_item(item_id)
    except ValueError as exc:
        code = str(exc)
        if code == "watchlist_not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=code) from exc
        if code in ("already_escalated", "watchlist_closed"):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=code) from exc
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=code) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "db_error", "message": str(exc)},
        ) from exc

    return EscalateResponse(
        item=WatchlistItem.model_validate(item),
        event_id=event_id,
    )
