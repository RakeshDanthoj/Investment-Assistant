"""Slow-burn editorial watchlist (P3-S1e / G-05)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

from psycopg.rows import dict_row

from app.db.connection import connection
from app.models.enums import EventCategory, LifecycleState

WatchlistStatus = Literal["watching", "escalated", "closed"]

WATCHLIST_SELECT = """
  id,
  event_description,
  category,
  added_at,
  review_frequency,
  last_reviewed_at,
  escalation_trigger,
  status,
  escalated_event_id
"""


def _row_to_dict(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    for key in ("id", "escalated_event_id"):
        if out.get(key) is not None:
            out[key] = str(out[key])
    for ts_key in ("added_at", "last_reviewed_at"):
        ts = out.get(ts_key)
        if isinstance(ts, datetime):
            eff = ts if ts.tzinfo else ts.replace(tzinfo=UTC)
            out[ts_key] = eff.astimezone(UTC).isoformat()
    return out


def list_watchlist_items(
    *,
    status: WatchlistStatus | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    lim = max(1, min(limit, 200))
    clauses = ["1=1"]
    params: list[Any] = []
    if status:
        clauses.append("status = %s")
        params.append(status)
    params.append(lim)
    sql = f"""
    SELECT {WATCHLIST_SELECT.strip()}
    FROM public.watchlist_items
    WHERE {' AND '.join(clauses)}
    ORDER BY
      CASE status WHEN 'watching' THEN 0 WHEN 'escalated' THEN 1 ELSE 2 END,
      added_at DESC
    LIMIT %s
    """
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, tuple(params))
        return [_row_to_dict(r) for r in cur.fetchall()]


def patch_watchlist_status(
    item_id: UUID,
    *,
    status: WatchlistStatus,
    touch_reviewed: bool = True,
) -> dict[str, Any] | None:
    reviewed_sql = ", last_reviewed_at = now()" if touch_reviewed else ""
    sql = f"""
    UPDATE public.watchlist_items
    SET status = %s{reviewed_sql}
    WHERE id = %s
    RETURNING {WATCHLIST_SELECT.strip()}
    """
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, (status, item_id))
        row = cur.fetchone()
        conn.commit()
    return _row_to_dict(row) if row else None


def escalate_watchlist_item(item_id: UUID) -> tuple[dict[str, Any], UUID]:
    """
    Create a draft event from a watchlist row and mark the item escalated.

    Returns (updated_item, event_id). Raises ValueError when not found or already escalated.
    """
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"""
            SELECT {WATCHLIST_SELECT.strip()}
            FROM public.watchlist_items
            WHERE id = %s
            FOR UPDATE
            """,
            (item_id,),
        )
        item = cur.fetchone()
        if not item:
            raise ValueError("watchlist_not_found")
        if item["status"] == "escalated" and item.get("escalated_event_id"):
            raise ValueError("already_escalated")
        if item["status"] == "closed":
            raise ValueError("watchlist_closed")

        category = EventCategory(str(item["category"]))
        title = str(item["event_description"])[:3800]
        canonical = f"watchlist:{item_id}"
        cur.execute(
            """
            INSERT INTO public.events (
              title,
              category,
              source_url,
              canonical_url,
              event_source,
              confidence_score,
              lifecycle_state,
              external_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (event_source, canonical_url) DO UPDATE
              SET title = EXCLUDED.title,
                  category = EXCLUDED.category
            RETURNING id
            """,
            (
                title,
                category.value,
                canonical,
                canonical,
                "watchlist",
                55,
                LifecycleState.DRAFT.value,
                f"watchlist-{item_id}",
            ),
        )
        event_row = cur.fetchone()
        if not event_row:
            raise RuntimeError("escalate_insert_failed")
        event_id = UUID(str(event_row["id"]))

        cur.execute(
            f"""
            UPDATE public.watchlist_items
            SET status = 'escalated',
                last_reviewed_at = now(),
                escalated_event_id = %s
            WHERE id = %s
            RETURNING {WATCHLIST_SELECT.strip()}
            """,
            (event_id, item_id),
        )
        updated = cur.fetchone()
        conn.commit()

    if not updated:
        raise RuntimeError("escalate_update_failed")
    return _row_to_dict(updated), event_id
