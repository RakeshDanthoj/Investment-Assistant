"""Lens query persistence and listing (P2-S6)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from psycopg.rows import dict_row

from app.db.connection import connection

LensQueryStatus = Literal["queued", "running", "done", "failed"]
_RECENT_LIMIT = 20
_MIN_QUERY_LEN = 11  # PRD: CTA enabled when input > 10 characters


@dataclass(frozen=True)
class LensQueryRow:
    id: UUID
    query: str
    sector: str | None
    horizon: str | None
    status: LensQueryStatus
    card_id: UUID | None
    created_at: datetime


def _parse_ts(value: object) -> datetime:
    if not isinstance(value, datetime):
        raise TypeError("expected datetime from lens_queries.created_at")
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def _row_from_record(record: dict) -> LensQueryRow:
    card_raw = record.get("card_id")
    return LensQueryRow(
        id=UUID(str(record["id"])),
        query=str(record["query"]),
        sector=str(record["sector"]) if record.get("sector") else None,
        horizon=str(record["horizon"]) if record.get("horizon") else None,
        status=record["status"],  # type: ignore[arg-type]
        card_id=UUID(str(card_raw)) if card_raw else None,
        created_at=_parse_ts(record["created_at"]),
    )


def create_query(
    *,
    user_id: UUID,
    query: str,
    sector: str | None,
    horizon: str | None,
) -> LensQueryRow:
    text = query.strip()
    if len(text) < _MIN_QUERY_LEN:
        raise ValueError("query_too_short")

    stmt = """
    INSERT INTO public.lens_queries (user_id, query, sector, horizon, status)
    VALUES (
      %s::uuid,
      %s,
      %s::public.event_category,
      %s,
      'queued'::public.lens_query_status
    )
    RETURNING id, query, sector::text, horizon, status::text, card_id, created_at
    """
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            stmt,
            (
                str(user_id),
                text,
                sector,
                horizon,
            ),
        )
        row = cur.fetchone()
    if row is None:
        raise RuntimeError("lens query insert returned no row")
    return _row_from_record(row)


def list_recent_for_user(user_id: UUID, *, limit: int = _RECENT_LIMIT) -> list[LensQueryRow]:
    capped = max(1, min(limit, _RECENT_LIMIT))
    stmt = """
    SELECT id, query, sector::text, horizon, status::text, card_id, created_at
    FROM public.lens_queries
    WHERE user_id = %s::uuid
    ORDER BY created_at DESC
    LIMIT %s
    """
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, (str(user_id), capped))
        rows = cur.fetchall()
    return [_row_from_record(dict(row)) for row in rows]


def get_query_for_user(*, user_id: UUID, query_id: UUID) -> LensQueryRow | None:
    stmt = """
    SELECT id, query, sector::text, horizon, status::text, card_id, created_at
    FROM public.lens_queries
    WHERE user_id = %s::uuid AND id = %s::uuid
    """
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, (str(user_id), str(query_id)))
        row = cur.fetchone()
    if row is None:
        return None
    return _row_from_record(dict(row))


def enqueue_generation(query_id: UUID) -> None:
    """Placeholder hook for P2-S7 pipeline worker; row is already status=queued."""
    _ = query_id
