"""Saved Thread collection — Lens Save to Thread (P2-S8)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel

from app.core.auth import CurrentUser
from app.services.saved_threads import SavedThreadRow, card_exists, list_for_user, save_card

router = APIRouter(prefix="/saved-threads", tags=["saved-threads"])


class SavedThreadCreate(BaseModel):
    card_id: UUID


class SavedThreadCreateResponse(BaseModel):
    card_id: UUID
    created: bool
    saved_at: datetime


class SavedThreadItem(BaseModel):
    card_id: UUID
    card_title: str
    event_category: str
    saved_at: datetime


class SavedThreadsListResponse(BaseModel):
    items: list[SavedThreadItem]


def _row_to_item(row: SavedThreadRow) -> SavedThreadItem:
    return SavedThreadItem(
        card_id=row.card_id,
        card_title=row.card_title,
        event_category=row.event_category,
        saved_at=row.saved_at,
    )


def _db_unavailable(exc: RuntimeError) -> None:
    if "SUPABASE_DB_URL" in str(exc):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "db_unavailable", "message": str(exc)},
        ) from exc
    raise exc


@router.post("", response_model=SavedThreadCreateResponse)
def post_saved_thread(
    body: SavedThreadCreate,
    current_user: CurrentUser,
    response: Response,
) -> SavedThreadCreateResponse:
    if not card_exists(body.card_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "card_not_found", "message": "Card not found"},
        )
    try:
        created, saved_at = save_card(
            user_id=UUID(current_user.id),
            card_id=body.card_id,
        )
    except RuntimeError as exc:
        _db_unavailable(exc)
    response.status_code = (
        status.HTTP_201_CREATED if created else status.HTTP_200_OK
    )
    return SavedThreadCreateResponse(
        card_id=body.card_id,
        created=created,
        saved_at=saved_at,
    )


@router.get("", response_model=SavedThreadsListResponse)
def get_saved_threads(current_user: CurrentUser) -> SavedThreadsListResponse:
    try:
        rows = list_for_user(UUID(current_user.id))
    except RuntimeError as exc:
        _db_unavailable(exc)
    return SavedThreadsListResponse(items=[_row_to_item(row) for row in rows])
