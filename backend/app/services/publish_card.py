"""Publish draft ICE cards + immutable track_record snapshot + profile-aware alerts (P1-S8)."""

from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from psycopg.rows import dict_row

from app.db.connection import connection
from app.models.enums import LifecycleState
from app.services.card_repository import (
    fetch_card_detail_for_review,
    fetch_instrument_assessments_for_card,
    fetch_signals_for_card,
)


class PublishCardError(ValueError):
    """Business-rule violation while publishing a card."""


def publish_draft_card(
    card_id: UUID,
    *,
    editor_review_seconds: int | None = None,
) -> dict[str, Any]:
    detail = fetch_card_detail_for_review(card_id)
    if detail is None:
        raise LookupError(f"card not found: {card_id}")
    if str(detail["lifecycle_state"]) != LifecycleState.DRAFT.value:
        raise PublishCardError("only draft cards can be published")

    seconds = editor_review_seconds
    if seconds is not None and seconds < 0:
        seconds = None

    signals = fetch_signals_for_card(card_id)
    instruments_snapshot = fetch_instrument_assessments_for_card(card_id)
    ev_layer = detail["evidence_layer"]
    if isinstance(ev_layer, str):
        ev_layer = json.loads(ev_layer) if ev_layer.strip() else {}
    if not isinstance(ev_layer, dict):
        ev_layer = {}

    payload_obj: dict[str, Any] = {
        "kind": "initial_publish",
        "editor_review_seconds": seconds,
        "card_title": detail["title"],
        "event_category": detail["event_category"],
        "signals_snapshot": signals,
        "ice_snapshot": {
            "title": detail["title"],
            "insight_layer": detail["insight_layer"],
            "context_layer": detail["context_layer"],
            "evidence_layer": ev_layer,
            "dissenting_view": detail["dissenting_view"],
            "framework_behind_this": detail["framework_behind_this"],
            "instruments": instruments_snapshot,
            "event_title": detail["event_title"],
            "event_confidence_score": detail["event_confidence_score"],
            "lifecycle_state": str(detail["lifecycle_state"]),
        },
    }
    notify_payload = json.dumps(
        {
            "card_title": detail["title"],
            "event_category": detail["event_category"],
        }
    )

    category = str(detail["event_category"])

    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        with conn.transaction():
            cur.execute(
                """
                UPDATE public.cards
                SET lifecycle_state = %s, updated_at = now()
                WHERE id = %s AND lifecycle_state = %s
                RETURNING id
                """,
                (
                    LifecycleState.PUBLISHED.value,
                    str(card_id),
                    LifecycleState.DRAFT.value,
                ),
            )
            if cur.fetchone() is None:
                raise PublishCardError("publish raced or card was not draft")

            cur.execute(
                """
                UPDATE public.events
                SET lifecycle_state = %s
                WHERE id = %s
                """,
                (LifecycleState.PUBLISHED.value, str(detail["event_id"])),
            )

            cur.execute(
                """
                INSERT INTO public.track_record (card_id, payload)
                VALUES (%s, %s::jsonb)
                """,
                (str(card_id), json.dumps(payload_obj)),
            )

            cur.execute(
                """
                INSERT INTO public.in_app_notifications (user_id, card_id, kind, payload)
                SELECT sp.user_id, %s::uuid, 'card_published', %s::jsonb
                FROM public.session_profiles sp
                WHERE sp.user_id IS NOT NULL
                  AND (
                    sp.notify_categories IS NULL
                    OR COALESCE(array_length(sp.notify_categories, 1), 0) = 0
                    OR %s = ANY(sp.notify_categories)
                  )
                """,
                (str(card_id), notify_payload, category),
            )

    return {"card_id": str(card_id), "lifecycle_state": LifecycleState.PUBLISHED.value}


__all__ = ["PublishCardError", "publish_draft_card"]
