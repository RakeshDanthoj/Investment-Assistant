"""Instrument lookup for holdings typeahead (P2-S9)."""

from __future__ import annotations

from typing import Any

from psycopg.rows import dict_row

from app.db.connection import connection


def search_instruments(query: str, *, limit: int = 10) -> list[dict[str, Any]]:
    q = query.strip()
    if not q:
        return []
    pattern = f"%{q}%"
    stmt = """
    SELECT
      ticker AS instrument_id,
      display_name,
      exchange
    FROM public.instruments
    WHERE ticker ILIKE %s OR display_name ILIKE %s
    ORDER BY
      CASE WHEN ticker ILIKE %s THEN 0 ELSE 1 END,
      ticker
    LIMIT %s
    """
    prefix = f"{q}%"
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, (pattern, pattern, prefix, limit))
        return [dict(r) for r in cur.fetchall()]
