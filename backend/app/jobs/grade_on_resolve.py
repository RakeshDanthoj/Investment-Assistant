"""Grade user predictions when a card enters resolved lifecycle (P2-S2)."""

from __future__ import annotations

import json
import logging
from uuid import UUID

from psycopg.rows import dict_row

from app.db.connection import connection
from app.models.enums import LifecycleState
from app.services.card_repository import (
    fetch_card_detail_for_review,
    fetch_track_record_initial_publish,
)
from app.services.notify_on_grade import fan_out_on_grade
from app.services.prediction_grader import (
    PROMPT_GRADING_VERSION,
    GradeResult,
    SupportsGradingCompletion,
    grade,
)
from app.services.reasoning_gap_detector import recompute_for_user

_LOG = logging.getLogger(__name__)

_RESOLVABLE_LIFECYCLE_STATES: frozenset[str] = frozenset(
    {
        LifecycleState.PUBLISHED.value,
        LifecycleState.ACTIVE.value,
        LifecycleState.SIGNAL_TRIGGERED.value,
        LifecycleState.THESIS_CONFIRMED.value,
        LifecycleState.THESIS_WEAKENED.value,
    }
)


def _fetch_ungraded_predictions(cur, card_id: str) -> list[dict]:
    cur.execute(
        """
        SELECT id, user_id, prediction_text
        FROM public.user_predictions
        WHERE card_id = %s::uuid
          AND mechanism_accuracy IS NULL
        ORDER BY logged_at ASC
        """,
        (card_id,),
    )
    return [dict(r) for r in cur.fetchall()]


def _persist_grade(
    cur,
    *,
    prediction_id: str,
    user_id: str,
    card_id: str,
    result: GradeResult,
) -> bool:
    cur.execute(
        """
        UPDATE public.user_predictions
        SET mechanism_accuracy = %s,
            business_accuracy = %s,
            market_accuracy = %s,
            gap_insight = %s
        WHERE id = %s::uuid
          AND mechanism_accuracy IS NULL
        """,
        (
            result.mechanism_accuracy,
            result.business_accuracy,
            result.market_accuracy,
            result.gap_insight,
            prediction_id,
        ),
    )
    if cur.rowcount != 1:
        return False

    tr_payload = {
        "kind": "prediction_grade",
        "user_id": user_id,
        "prediction_id": prediction_id,
        "mechanism_accuracy": result.mechanism_accuracy,
        "business_accuracy": result.business_accuracy,
        "market_accuracy": result.market_accuracy,
        "gap_insight": result.gap_insight,
        "prompt_version": PROMPT_GRADING_VERSION,
        "source": "grade_on_resolve",
    }
    cur.execute(
        """
        INSERT INTO public.track_record (card_id, payload)
        VALUES (%s::uuid, %s::jsonb)
        """,
        (card_id, json.dumps(tr_payload)),
    )
    return True


def grade_predictions_for_card(
    card_id: UUID,
    *,
    llm: SupportsGradingCompletion | None = None,
) -> int:
    """
    Grade all ungraded predictions for a resolved card. Idempotent: already-graded rows skipped.
    Returns count of newly graded predictions.
    """
    detail = fetch_card_detail_for_review(card_id)
    if detail is None:
        raise LookupError(f"card not found: {card_id}")
    if str(detail["lifecycle_state"]) != LifecycleState.RESOLVED.value:
        raise ValueError("card_must_be_resolved")

    original = fetch_track_record_initial_publish(card_id)
    if original is None:
        raise ValueError("original_publish_snapshot_missing")

    graded = 0
    graded_user_ids: list[str] = []
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        rows = _fetch_ungraded_predictions(cur, str(card_id))
        for row in rows:
            result = grade(
                prediction_text=str(row["prediction_text"]),
                original_publish=original,
                final_card=detail,
                llm=llm,
            )
            if _persist_grade(
                cur,
                prediction_id=str(row["id"]),
                user_id=str(row["user_id"]),
                card_id=str(card_id),
                result=result,
            ):
                graded += 1
                graded_user_ids.append(str(row["user_id"]))
        if graded_user_ids:
            fan_out_on_grade(cur, card_id=str(card_id), user_ids=graded_user_ids)
        conn.commit()

    for uid in set(graded_user_ids):
        try:
            recompute_for_user(UUID(uid))
        except Exception:
            _LOG.exception("reasoning_gap.recompute_failed", extra={"user_id": uid})

    if graded:
        _LOG.info("grade_on_resolve.complete", extra={"card_id": str(card_id), "graded": graded})
    return graded


def transition_card_to_resolved(
    card_id: UUID,
    *,
    llm: SupportsGradingCompletion | None = None,
) -> dict[str, int | str]:
    """
    Editorial hook: move card to ``resolved`` then grade all pending predictions.
  """
    cid = str(card_id)
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            UPDATE public.cards
            SET lifecycle_state = %s, updated_at = now()
            WHERE id = %s::uuid
              AND lifecycle_state::text = ANY(%s::text[])
            RETURNING id
            """,
            (
                LifecycleState.RESOLVED.value,
                cid,
                list(_RESOLVABLE_LIFECYCLE_STATES),
            ),
        )
        updated = cur.fetchone()
        if updated is None:
            cur.execute(
                "SELECT lifecycle_state::text FROM public.cards WHERE id = %s::uuid",
                (cid,),
            )
            existing = cur.fetchone()
            if existing is None:
                raise LookupError(f"card not found: {card_id}")
            state = str(existing["lifecycle_state"])
            if state != LifecycleState.RESOLVED.value:
                raise ValueError(f"card_not_resolvable_from_{state}")
        conn.commit()

    count = grade_predictions_for_card(card_id, llm=llm)
    return {"card_id": cid, "graded": count}


__all__ = [
    "grade_predictions_for_card",
    "transition_card_to_resolved",
]
