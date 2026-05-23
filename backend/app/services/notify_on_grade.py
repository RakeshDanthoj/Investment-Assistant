"""Fan-out in-app notifications when predictions are graded (P2-S3)."""

from __future__ import annotations

import json
from typing import Any


def fan_out_on_grade(
    cur,
    *,
    card_id: str,
    user_ids: list[str],
) -> int:
    """
    Insert one unread ``card_graded`` notification per user who was just graded.
    Skips users who already have an unread notification for this card.
    Returns number of rows inserted.
    """
    if not user_ids:
        return 0

    cur.execute(
        """
        SELECT c.title AS card_title,
               e.title AS event_title,
               c.updated_at AS resolved_at
        FROM public.cards c
        JOIN public.events e ON e.id = c.event_id
        WHERE c.id = %s::uuid
        """,
        (card_id,),
    )
    meta = cur.fetchone()
    if meta is None:
        return 0

    card_title = str(meta["card_title"])
    event_title = str(meta["event_title"])
    resolved_at = meta["resolved_at"]
    resolved_iso = resolved_at.isoformat() if resolved_at is not None else None

    cur.execute(
        """
        INSERT INTO public.in_app_notifications (user_id, card_id, kind, payload)
        SELECT up.user_id,
               %s::uuid,
               'card_graded',
               %s::jsonb
        FROM public.user_predictions up
        WHERE up.card_id = %s::uuid
          AND up.user_id = ANY(%s::uuid[])
          AND up.mechanism_accuracy IS NOT NULL
          AND NOT EXISTS (
            SELECT 1
            FROM public.in_app_notifications n
            WHERE n.user_id = up.user_id
              AND n.card_id = %s::uuid
              AND n.kind = 'card_graded'
              AND n.read_at IS NULL
          )
        RETURNING id
        """,
        (
            card_id,
            json.dumps(
                {
                    "card_title": card_title,
                    "event_title": event_title,
                    "resolved_at": resolved_iso,
                }
            ),
            card_id,
            user_ids,
            card_id,
        ),
    )
    return cur.rowcount


def list_unread_card_graded(cur, user_id: str) -> list[dict[str, Any]]:
    cur.execute(
        """
        SELECT n.id,
               n.card_id,
               n.payload,
               n.created_at,
               up.id AS prediction_id
        FROM public.in_app_notifications n
        INNER JOIN public.user_predictions up
          ON up.card_id = n.card_id
         AND up.user_id = n.user_id
        WHERE n.user_id = %s::uuid
          AND n.kind = 'card_graded'
          AND n.read_at IS NULL
        ORDER BY n.created_at DESC
        """,
        (user_id,),
    )
    return [dict(row) for row in cur.fetchall()]


def mark_notification_read(cur, *, notification_id: str, user_id: str) -> bool:
    cur.execute(
        """
        UPDATE public.in_app_notifications
        SET read_at = now()
        WHERE id = %s::uuid
          AND user_id = %s::uuid
          AND kind = 'card_graded'
          AND read_at IS NULL
        """,
        (notification_id, user_id),
    )
    return cur.rowcount == 1


__all__ = ["fan_out_on_grade", "list_unread_card_graded", "mark_notification_read"]
