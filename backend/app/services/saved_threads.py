"""Persist Lens cards to a user's Thread collection (P2-S8)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from psycopg.rows import dict_row

from app.db.connection import connection


@dataclass(frozen=True)
class SavedThreadRow:
    card_id: UUID
    card_title: str
    event_category: str
    saved_at: datetime


def _parse_ts(value: object) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("expected datetime from saved_threads.saved_at")
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def save_card(*, user_id: UUID, card_id: UUID) -> tuple[bool, datetime]:
    """
    Insert a saved thread row. Returns (created, saved_at).
    Idempotent: duplicate (user_id, card_id) returns (False, existing saved_at).
    """
    insert_stmt = """
    INSERT INTO public.saved_threads (user_id, card_id)
    VALUES (%s::uuid, %s::uuid)
    ON CONFLICT (user_id, card_id) DO NOTHING
    RETURNING saved_at
    """
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(insert_stmt, (str(user_id), str(card_id)))
        row = cur.fetchone()
        if row is not None:
            return True, _parse_ts(row["saved_at"])

        cur.execute(
            """
            SELECT saved_at
            FROM public.saved_threads
            WHERE user_id = %s::uuid AND card_id = %s::uuid
            """,
            (str(user_id), str(card_id)),
        )
        existing = cur.fetchone()
    if existing is None:
        raise RuntimeError("saved_threads conflict without existing row")
    return False, _parse_ts(existing["saved_at"])


def list_for_user(user_id: UUID, *, limit: int = 50) -> list[SavedThreadRow]:
    capped = max(1, min(limit, 100))
    stmt = """
    SELECT
      st.card_id,
      COALESCE(c.title, e.title, 'Untitled card') AS card_title,
      e.category::text AS event_category,
      st.saved_at
    FROM public.saved_threads st
    INNER JOIN public.cards c ON c.id = st.card_id
    INNER JOIN public.events e ON e.id = c.event_id
    WHERE st.user_id = %s::uuid
    ORDER BY st.saved_at DESC
    LIMIT %s
    """
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, (str(user_id), capped))
        rows = cur.fetchall()

    return [
        SavedThreadRow(
            card_id=UUID(str(row["card_id"])),
            card_title=str(row["card_title"]),
            event_category=str(row["event_category"]),
            saved_at=_parse_ts(row["saved_at"]),
        )
        for row in rows
    ]


def card_exists(card_id: UUID) -> bool:
    stmt = "SELECT 1 FROM public.cards WHERE id = %s::uuid LIMIT 1"
    with connection() as conn, conn.cursor() as cur:
        cur.execute(stmt, (str(card_id),))
        return cur.fetchone() is not None
