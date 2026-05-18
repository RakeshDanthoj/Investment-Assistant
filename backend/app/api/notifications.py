"""Authenticated in-app notifications (P1-S11 signal badge + P1-S8 publish)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter
from psycopg.rows import dict_row
from pydantic import BaseModel

from app.core.auth import CurrentUser
from app.db.connection import connection

router = APIRouter(tags=["notifications"])


class NotificationItem(BaseModel):
    id: UUID
    card_id: UUID
    kind: str
    payload: dict[str, Any]
    created_at: datetime


class NotificationsResponse(BaseModel):
    items: list[NotificationItem]
    count: int


@router.get("/notifications", response_model=NotificationsResponse)
def list_notifications(
    current_user: CurrentUser,
    limit: int = 30,
) -> NotificationsResponse:
    lim = max(1, min(limit, 100))
    stmt = """
    SELECT id, card_id, kind, payload, created_at
    FROM public.in_app_notifications
    WHERE user_id = %s::uuid
    ORDER BY created_at DESC
    LIMIT %s
    """
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, (current_user.id, lim))
        rows = cur.fetchall()

    items: list[NotificationItem] = []
    for row in rows:
        rid = row["id"]
        cid = row["card_id"]
        ts = row["created_at"]
        if isinstance(ts, datetime):
            ts_eff = ts if ts.tzinfo else ts.replace(tzinfo=UTC)
        else:
            continue
        items.append(
            NotificationItem(
                id=UUID(str(rid)),
                card_id=UUID(str(cid)),
                kind=str(row["kind"]),
                payload=dict(row["payload"]) if row.get("payload") else {},
                created_at=ts_eff,
            )
        )
    return NotificationsResponse(items=items, count=len(items))
