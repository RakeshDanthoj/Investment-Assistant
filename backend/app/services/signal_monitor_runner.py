"""Orchestrates signal monitoring, gate routing, persistence, and fan-out (P1-S11)."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from psycopg.rows import dict_row

from app.db.connection import connection
from app.models.enums import LifecycleState, SignalState
from app.services.confidence_gate import GateDecision, route
from app.services.email_on_signal import fan_out as fan_out_signal_emails
from app.services.market_facts import build_market_facts
from app.services.signal_check import MarketFact, SignalEvalResult, evaluate

_LOG = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")


def ist_market_session_open(reference_time: datetime | None = None) -> bool:
    """NSE/BSE equity cash session (Mon–Fri), 09:15–15:30 IST inclusive."""
    ref = reference_time or datetime.now(tz=UTC)
    ist = ref.astimezone(IST)
    if ist.weekday() >= 5:
        return False
    minutes = ist.hour * 60 + ist.minute
    open_min = 9 * 60 + 15
    close_min = 15 * 60 + 30
    return open_min <= minutes <= close_min


SourcesProvider = Callable[[datetime], Sequence[MarketFact]]


@dataclass
class MonitorSummary:
    cards_scanned: int = 0
    signals_checked: int = 0
    high_actions: int = 0
    medium_actions: int = 0
    low_actions: int = 0
    skipped_market_hours: bool = False
    skipped_no_db: bool = False


def _sources_json(eval_result: SignalEvalResult) -> str:
    payload = {
        "direct": list(eval_result.direct_source_ids),
        "partial": list(eval_result.partial_source_ids),
    }
    return json.dumps(payload)


def _log_gate(
    cur,
    *,
    card_id: str,
    signal_id: str,
    decision: GateDecision,
    eval_result: SignalEvalResult,
) -> None:
    cur.execute(
        """
        INSERT INTO public.confidence_gate_log (card_id, signal_id, gate, reason, sources)
        VALUES (%s::uuid, %s::uuid, %s, %s, %s::jsonb)
        """,
        (card_id, signal_id, decision.tier, decision.reason, _sources_json(eval_result)),
    )


def _fan_out_signal_notifications(cur, *, card_id: str, card_title: str, signal_text: str) -> None:
    payload = json.dumps(
        {
            "card_title": card_title,
            "signal_excerpt": signal_text[:280],
        }
    )
    cur.execute(
        """
        INSERT INTO public.in_app_notifications (user_id, card_id, kind, payload)
        SELECT up.user_id, %s::uuid, 'signal_fired', %s::jsonb
        FROM public.user_predictions up
        WHERE up.card_id = %s::uuid
        """,
        (card_id, payload, card_id),
    )


def _high_path(
    cur,
    *,
    card_id: str,
    signal_id: str,
    signal_text: str,
    card_title: str,
    decision: GateDecision,
    eval_result: SignalEvalResult,
    emit_email: bool = True,
) -> None:
    del signal_text
    override_until = datetime.now(tz=UTC) + timedelta(hours=2)
    note = (
        f"\n\n[Auto-update — high confidence] Signal matched market/macro sources "
        f"({decision.reason}). Editors may override until {override_until.isoformat()}."
    )
    cur.execute(
        """
        UPDATE public.cards
        SET lifecycle_state = %s,
            editor_override_deadline = %s,
            insight_layer = insight_layer || %s,
            updated_at = now()
        WHERE id = %s::uuid
        """,
        (
            LifecycleState.SIGNAL_TRIGGERED.value,
            override_until,
            note[:4000],
            card_id,
        ),
    )
    cur.execute(
        """
        UPDATE public.signals
        SET state = %s, triggered_at = now()
        WHERE id = %s::uuid AND card_id = %s::uuid
        """,
        (SignalState.TRIGGERED.value, signal_id, card_id),
    )
    tr_payload = {
        "kind": "signal_auto_update",
        "signal_id": signal_id,
        "gate": decision.tier,
        "reason": decision.reason,
        "sources": json.loads(_sources_json(eval_result)),
        "editor_override_deadline": override_until.isoformat(),
    }
    cur.execute(
        """
        INSERT INTO public.track_record (card_id, payload)
        VALUES (%s::uuid, %s::jsonb)
        """,
        (card_id, json.dumps(tr_payload)),
    )
    if emit_email:
        fan_out_signal_emails(
            cur,
            card_id=card_id,
            signal_id=signal_id,
            card_title=card_title,
        )


def _medium_path(
    cur,
    *,
    card_id: str,
    signal_id: str,
    decision: GateDecision,
    eval_result: SignalEvalResult,
) -> None:
    payload = {
        "gate": decision.tier,
        "reason": decision.reason,
        "sources": json.loads(_sources_json(eval_result)),
    }
    cur.execute(
        """
        INSERT INTO public.editorial_signal_queue (card_id, signal_id, gate, reason, payload)
        VALUES (%s::uuid, %s::uuid, %s, %s, %s::jsonb)
        ON CONFLICT (card_id, signal_id) DO UPDATE SET
          reason = EXCLUDED.reason,
          payload = EXCLUDED.payload,
          status = 'pending',
          created_at = now()
        """,
        (card_id, signal_id, decision.tier, decision.reason, json.dumps(payload)),
    )


def _low_path(
    cur,
    *,
    card_id: str,
    signal_id: str,
    decision: GateDecision,
    eval_result: SignalEvalResult,
) -> None:
    summary = f"low_gate:{decision.reason}"
    payload = {"sources": json.loads(_sources_json(eval_result))}
    cur.execute(
        """
        INSERT INTO public.digest_log (card_id, signal_id, gate, summary, payload)
        VALUES (%s::uuid, %s::uuid, %s, %s, %s::jsonb)
        """,
        (card_id, signal_id, decision.tier, summary[:2000], json.dumps(payload)),
    )


def run_signal_monitor(
    *,
    reference_time: datetime | None = None,
    skip_market_hours_check: bool = False,
    facts_provider: SourcesProvider | None = None,
    emit_notifications: bool = True,
    only_card_id: UUID | None = None,
) -> MonitorSummary:
    summary = MonitorSummary()
    ref = reference_time or datetime.now(tz=UTC)
    if ref.tzinfo is None:
        ref = ref.replace(tzinfo=UTC)

    if not skip_market_hours_check and not ist_market_session_open(ref):
        summary.skipped_market_hours = True
        _LOG.info("signal_monitor.skipped_outside_ist_window")
        return summary

    if facts_provider is None:

        def facts_fn(rt: datetime) -> Sequence[MarketFact]:
            return build_market_facts(reference_time=rt)

    else:
        facts_fn = facts_provider

    try:
        facts = list(facts_fn(ref))
    except RuntimeError:
        summary.skipped_no_db = True
        _LOG.warning("signal_monitor.skipped_no_db_url")
        return summary

    eligible_states = [
        LifecycleState.PUBLISHED.value,
        LifecycleState.ACTIVE.value,
        LifecycleState.SIGNAL_TRIGGERED.value,
    ]
    stmt = """
    SELECT
      s.id AS signal_id,
      s.card_id,
      s.signal_text,
      c.title AS card_title,
      c.lifecycle_state::text AS lifecycle_state
    FROM public.signals s
    INNER JOIN public.cards c ON c.id = s.card_id
    WHERE s.state = %s
      AND c.lifecycle_state = ANY(%s)
    """
    params: list = [SignalState.PENDING.value, eligible_states]
    if only_card_id is not None:
        stmt += " AND c.id = %s::uuid"
        params.append(str(only_card_id))
    stmt += " ORDER BY s.created_at ASC"

    try:
        with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(stmt, tuple(params))
            rows = [dict(r) for r in cur.fetchall()]
    except RuntimeError:
        summary.skipped_no_db = True
        _LOG.warning("signal_monitor.skipped_no_db_url")
        return summary

    cards_seen = {str(r["card_id"]) for r in rows}
    summary.cards_scanned = len(cards_seen)

    for row in rows:
        signal_id = str(row["signal_id"])
        card_id = str(row["card_id"])
        signal_text = str(row["signal_text"] or "")
        card_title = str(row["card_title"] or "")
        eval_result = evaluate(signal_text, facts, reference_time=ref)
        summary.signals_checked += 1

        if eval_result.status == "none":
            continue

        decision = route(eval_result)

        try:
            with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
                with conn.transaction():
                    if decision.tier == "low":
                        cur.execute(
                            """
                            SELECT 1 FROM public.digest_log
                            WHERE signal_id = %s::uuid LIMIT 1
                            """,
                            (signal_id,),
                        )
                        if cur.fetchone() is not None:
                            continue

                    _log_gate(
                        cur,
                        card_id=card_id,
                        signal_id=signal_id,
                        decision=decision,
                        eval_result=eval_result,
                    )

                    queue_existed = False
                    if decision.tier == "high":
                        _high_path(
                            cur,
                            card_id=card_id,
                            signal_id=signal_id,
                            signal_text=signal_text,
                            card_title=card_title,
                            decision=decision,
                            eval_result=eval_result,
                        )
                        summary.high_actions += 1
                    elif decision.tier == "medium":
                        cur.execute(
                            """
                            SELECT 1 FROM public.editorial_signal_queue
                            WHERE signal_id = %s::uuid LIMIT 1
                            """,
                            (signal_id,),
                        )
                        queue_existed = cur.fetchone() is not None
                        _medium_path(
                            cur,
                            card_id=card_id,
                            signal_id=signal_id,
                            decision=decision,
                            eval_result=eval_result,
                        )
                        summary.medium_actions += 1
                    else:
                        _low_path(
                            cur,
                            card_id=card_id,
                            signal_id=signal_id,
                            decision=decision,
                            eval_result=eval_result,
                        )
                        summary.low_actions += 1

                    do_notify = emit_notifications
                    if decision.tier == "medium" and queue_existed:
                        do_notify = False
                    if do_notify:
                        _fan_out_signal_notifications(
                            cur,
                            card_id=card_id,
                            card_title=card_title,
                            signal_text=signal_text,
                        )
        except RuntimeError:
            summary.skipped_no_db = True
            _LOG.warning("signal_monitor.db_lost_mid_run")
            return summary

    _LOG.info(
        "signal_monitor.complete",
        extra={
            "signals_checked": summary.signals_checked,
            "high": summary.high_actions,
            "medium": summary.medium_actions,
            "low": summary.low_actions,
        },
    )
    return summary


__all__ = [
    "MonitorSummary",
    "ist_market_session_open",
    "run_signal_monitor",
]
