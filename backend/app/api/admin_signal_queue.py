"""Editorial queue for medium-confidence signal hits (P1-S11)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter
from psycopg.rows import dict_row
from pydantic import BaseModel

from app.db.connection import connection

router = APIRouter(tags=["admin-signal-queue"])


class EditorialSignalRow(BaseModel):
    id: UUID
    card_id: UUID
    signal_id: UUID
    status: str
    gate: str
    reason: str
    payload: dict[str, Any]
    created_at: datetime


@router.get("/signal-queue", response_model=list[EditorialSignalRow])
def list_pending_signal_queue(
    status: str = "pending",
    limit: int = 100,
) -> list[EditorialSignalRow]:
    lim = max(1, min(limit, 200))
    stmt = """
    SELECT id, card_id, signal_id, status, gate, reason, payload, created_at
    FROM public.editorial_signal_queue
    WHERE status = %s
    ORDER BY created_at DESC
    LIMIT %s
    """
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, (status, lim))
        rows = cur.fetchall()

    out: list[EditorialSignalRow] = []
    for row in rows:
        ts = row["created_at"]
        if isinstance(ts, datetime):
            ts_eff = ts if ts.tzinfo else ts.replace(tzinfo=UTC)
        else:
            continue
        out.append(
            EditorialSignalRow(
                id=UUID(str(row["id"])),
                card_id=UUID(str(row["card_id"])),
                signal_id=UUID(str(row["signal_id"])),
                status=str(row["status"]),
                gate=str(row["gate"]),
                reason=str(row["reason"] or ""),
                payload=dict(row["payload"]) if row.get("payload") else {},
                created_at=ts_eff,
            )
        )
    return out
