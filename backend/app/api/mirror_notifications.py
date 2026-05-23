"""Mirror graded-card notifications (P2-S3)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from psycopg.rows import dict_row
from pydantic import BaseModel

from app.core.auth import CurrentUser
from app.db.connection import connection
from app.services.notify_on_grade import list_unread_card_graded, mark_notification_read

router = APIRouter()


class MirrorNotificationItem(BaseModel):
    id: UUID
    card_id: UUID
    prediction_id: UUID
    event_title: str
    card_title: str
    resolved_at: datetime | None = None
    created_at: datetime


class MirrorUnreadNotificationsResponse(BaseModel):
    count: int
    items: list[MirrorNotificationItem]


class MarkReadResponse(BaseModel):
    ok: bool


def _parse_ts(value: object) -> datetime | None:
    if not isinstance(value, datetime):
        return None
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _row_to_item(row: dict[str, Any]) -> MirrorNotificationItem | None:
    payload = dict(row.get("payload") or {})
    created = _parse_ts(row.get("created_at"))
    if created is None:
        return None
    resolved_raw = payload.get("resolved_at")
    resolved_at: datetime | None = None
    if isinstance(resolved_raw, str) and resolved_raw:
        try:
            resolved_at = datetime.fromisoformat(resolved_raw.replace("Z", "+00:00"))
            if resolved_at.tzinfo is None:
                resolved_at = resolved_at.replace(tzinfo=UTC)
        except ValueError:
            resolved_at = None
    return MirrorNotificationItem(
        id=UUID(str(row["id"])),
        card_id=UUID(str(row["card_id"])),
        prediction_id=UUID(str(row["prediction_id"])),
        event_title=str(payload.get("event_title") or ""),
        card_title=str(payload.get("card_title") or ""),
        resolved_at=resolved_at,
        created_at=created,
    )


@router.get("/notifications/unread", response_model=MirrorUnreadNotificationsResponse)
def get_unread_mirror_notifications(current_user: CurrentUser) -> MirrorUnreadNotificationsResponse:
    try:
        with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            rows = list_unread_card_graded(cur, current_user.id)
    except RuntimeError as exc:
        if "SUPABASE_DB_URL" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"code": "db_unavailable", "message": str(exc)},
            ) from exc
        raise

    items: list[MirrorNotificationItem] = []
    for row in rows:
        item = _row_to_item(row)
        if item is not None:
            items.append(item)
    return MirrorUnreadNotificationsResponse(count=len(items), items=items)


@router.post("/notifications/{notification_id}/read", response_model=MarkReadResponse)
def mark_mirror_notification_read(
    notification_id: UUID,
    current_user: CurrentUser,
) -> MarkReadResponse:
    try:
        with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            ok = mark_notification_read(
                cur,
                notification_id=str(notification_id),
                user_id=current_user.id,
            )
            conn.commit()
    except RuntimeError as exc:
        if "SUPABASE_DB_URL" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"code": "db_unavailable", "message": str(exc)},
            ) from exc
        raise

    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="notification_not_found")
    return MarkReadResponse(ok=True)
