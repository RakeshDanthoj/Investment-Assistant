"""Persist ICE cards + child rows via Postgres (same DB as Factor DB)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from psycopg.rows import dict_row

from app.db.connection import connection
from app.models.enums import LifecycleState, SignalState


def fetch_event_row(event_id: UUID) -> dict[str, Any] | None:
    stmt = """
    SELECT
      id, title, category, source_url, canonical_url, event_source,
      confidence_score, lifecycle_state, prompt_version, created_at
    FROM public.events
    WHERE id = %s
    LIMIT 1
    """
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, (event_id,))
        row = cur.fetchone()
    return dict(row) if row else None


def insert_draft_card_bundle(
    *,
    event_id: UUID,
    title: str,
    insight_layer: str,
    context_layer: str,
    evidence_layer: dict[str, Any],
    dissenting_view: str,
    framework_behind_this: str,
    prompt_version: str,
    llm_input_tokens: int,
    llm_output_tokens: int,
    llm_cost_usd: float,
    signals: list[dict[str, str]],
    instrument_assessments: list[dict[str, Any]],
) -> UUID:
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        with conn.transaction():
            cur.execute(
                """
                INSERT INTO public.cards (
                  event_id, title, insight_layer, context_layer, evidence_layer,
                  dissenting_view, framework_behind_this, prompt_version,
                  lifecycle_state, llm_input_tokens, llm_output_tokens, llm_cost_usd
                )
                VALUES (
                  %s,%s,%s,%s,%s::jsonb,
                  %s,%s,%s,
                  %s,%s,%s,%s
                )
                RETURNING id
                """,
                (
                    str(event_id),
                    title[:7800],
                    insight_layer,
                    context_layer,
                    json.dumps(evidence_layer),
                    dissenting_view,
                    framework_behind_this,
                    prompt_version[:500],
                    LifecycleState.DRAFT.value,
                    llm_input_tokens,
                    llm_output_tokens,
                    llm_cost_usd,
                ),
            )
            cid_row = cur.fetchone()
            if not cid_row:
                raise RuntimeError("card insert returned no id")
            card_id = UUID(str(cid_row["id"]))

            for sig in signals:
                st = (sig.get("signal_text") or "").strip()
                if not st:
                    continue
                cur.execute(
                    """
                    INSERT INTO public.signals (card_id, signal_text, state)
                    VALUES (%s, %s, %s)
                    """,
                    (str(card_id), st[:7800], SignalState.PENDING.value),
                )

            for row in instrument_assessments:
                ticker = (row.get("instrument_id") or "").strip().upper()
                if not ticker:
                    continue
                cur.execute(
                    """
                    INSERT INTO public.instrument_assessments (
                      card_id, version, instrument_id, signal_type, reasoning,
                      entry_conditions, exit_conditions
                    )
                    VALUES (%s, 1, %s, %s, %s, %s, %s)
                    """,
                    (
                        str(card_id),
                        ticker[:32],
                        (row.get("signal_type") or "watch").strip().lower()[:32],
                        (row.get("reasoning") or "").strip() or None,
                        list(row.get("entry_conditions") or []),
                        list(row.get("exit_conditions") or []),
                    ),
                )

    return card_id


def fetch_card_detail_for_review(card_id: UUID) -> dict[str, Any] | None:
    stmt = """
    SELECT
      c.id AS card_id,
      c.event_id,
      c.title,
      c.insight_layer,
      c.context_layer,
      c.evidence_layer,
      c.dissenting_view,
      c.framework_behind_this,
      c.prompt_version,
      c.lifecycle_state,
      c.created_at AS card_created_at,
      e.title AS event_title,
      e.category::text AS event_category,
      e.confidence_score AS event_confidence_score,
      e.lifecycle_state::text AS event_lifecycle_state,
      e.canonical_url AS event_canonical_url
    FROM public.cards c
    INNER JOIN public.events e ON e.id = c.event_id
    WHERE c.id = %s
    LIMIT 1
    """
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, (str(card_id),))
        row = cur.fetchone()
    return dict(row) if row else None


def archive_card(card_id: UUID) -> None:
    stmt = """
    UPDATE public.cards
    SET lifecycle_state = %s, updated_at = now()
    WHERE id = %s AND lifecycle_state = %s
    """
    with connection() as conn, conn.cursor() as cur:
        cur.execute(
            stmt,
            (
                LifecycleState.ARCHIVED.value,
                str(card_id),
                LifecycleState.DRAFT.value,
            ),
        )
        if cur.rowcount != 1:
            raise RuntimeError(f"archive_card expected one draft row, got {cur.rowcount}")


def fetch_signals_for_card(card_id: UUID) -> list[dict[str, Any]]:
    stmt = """
    SELECT signal_text, state::text AS state
    FROM public.signals
    WHERE card_id = %s
    ORDER BY created_at ASC
    """
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, (str(card_id),))
        rows = cur.fetchall()
    return [dict(r) for r in rows]


def fetch_track_record_initial_publish(card_id: UUID) -> dict[str, Any] | None:
    """First immutable Day-1 snapshot written at publish (P1-S10 Original View)."""
    stmt = """
    SELECT payload
    FROM public.track_record
    WHERE card_id = %s AND payload->>'kind' = 'initial_publish'
    ORDER BY logged_at ASC
    LIMIT 1
    """
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, (str(card_id),))
        row = cur.fetchone()
    if not row:
        return None
    pl = row.get("payload")
    return dict(pl) if isinstance(pl, dict) else None


def fetch_instrument_assessments_for_card(card_id: UUID) -> list[dict[str, Any]]:
    stmt = """
    SELECT instrument_id, signal_type, reasoning, entry_conditions, exit_conditions
    FROM public.instrument_assessments
    WHERE card_id = %s
    ORDER BY created_at ASC
    """
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, (str(card_id),))
        rows = cur.fetchall()
    return [dict(r) for r in rows]


@dataclass(frozen=True)
class CardDetailBundle:
    detail: dict[str, Any]
    signals: list[dict[str, Any]]
    instruments: list[dict[str, Any]]
    bias_flags: list[dict[str, Any]]


def fetch_card_detail_bundle(card_id: UUID) -> CardDetailBundle | None:
    """Fetch card detail, signals, instruments, and bias flags in one connection."""
    detail_stmt = """
    SELECT
      c.id AS card_id,
      c.event_id,
      c.title,
      c.insight_layer,
      c.context_layer,
      c.evidence_layer,
      c.dissenting_view,
      c.framework_behind_this,
      c.prompt_version,
      c.lifecycle_state,
      c.created_at AS card_created_at,
      e.title AS event_title,
      e.category::text AS event_category,
      e.confidence_score AS event_confidence_score,
      e.lifecycle_state::text AS event_lifecycle_state,
      e.canonical_url AS event_canonical_url
    FROM public.cards c
    INNER JOIN public.events e ON e.id = c.event_id
    WHERE c.id = %s
    LIMIT 1
    """
    signals_stmt = """
    SELECT signal_text, state::text AS state
    FROM public.signals
    WHERE card_id = %s
    ORDER BY created_at ASC
    """
    instruments_stmt = """
    SELECT instrument_id, signal_type, reasoning, entry_conditions, exit_conditions
    FROM public.instrument_assessments
    WHERE card_id = %s
    ORDER BY created_at ASC
    """
    bias_stmt = """
    SELECT bias_type, severity, description, detected_at
    FROM public.card_bias_flags
    WHERE card_id = %s
    ORDER BY bias_type
    """
    card_key = str(card_id)
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(detail_stmt, (card_key,))
        detail_row = cur.fetchone()
        if not detail_row:
            return None
        detail = dict(detail_row)

        cur.execute(signals_stmt, (card_key,))
        signals = [dict(r) for r in cur.fetchall()]

        cur.execute(instruments_stmt, (card_key,))
        instruments = [dict(r) for r in cur.fetchall()]

        cur.execute(bias_stmt, (card_key,))
        bias_flags = [dict(r) for r in cur.fetchall()]

    return CardDetailBundle(
        detail=detail,
        signals=signals,
        instruments=instruments,
        bias_flags=bias_flags,
    )
