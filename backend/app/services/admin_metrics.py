"""Aggregate PRD §13 ops metrics for the admin dashboard (P2-S13)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from psycopg.rows import dict_row

from app.db.connection import connection


def _p95(values: list[float]) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    idx = max(0, int(len(ordered) * 0.95) - 1)
    return round(ordered[idx], 2)


def fetch_admin_metrics(*, window_days: int = 30) -> dict:
    """
    Returns daily card count, p95 pipeline duration, high-confidence override rate,
    and signal false-positive rate (PRD §13).
    """
    now = datetime.now(tz=UTC)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    window_start = now - timedelta(days=window_days)

    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT COUNT(*)::int AS daily_card_count
            FROM public.cards
            WHERE created_at >= %s
            """,
            (day_start,),
        )
        daily_card_count = int(cur.fetchone()["daily_card_count"])

        cur.execute(
            """
            SELECT duration_ms::float AS duration_ms
            FROM public.pipeline_runs
            WHERE created_at >= %s AND status = 'ok'
            ORDER BY duration_ms
            """,
            (window_start,),
        )
        durations = [float(r["duration_ms"]) for r in cur.fetchall()]
        p95_generation_time_ms = _p95(durations)

        cur.execute(
            """
            SELECT
              COUNT(*)::int AS high_gate_total,
              COUNT(*) FILTER (
                WHERE c.updated_at > l.created_at + interval '5 minutes'
              )::int AS high_gate_overridden
            FROM public.confidence_gate_log l
            JOIN public.cards c ON c.id = l.card_id
            WHERE l.gate = 'high'
              AND l.created_at >= %s
            """,
            (window_start,),
        )
        gate_row = cur.fetchone()
        high_total = int(gate_row["high_gate_total"] or 0)
        high_overridden = int(gate_row["high_gate_overridden"] or 0)

    false_positive_rate: float | None = None
    override_rate: float | None = None
    if high_total > 0:
        rate = round(high_overridden / high_total, 4)
        false_positive_rate = rate
        override_rate = rate

    return {
        "as_of": now.isoformat(),
        "window_days": window_days,
        "daily_card_count": daily_card_count,
        "p95_generation_time_ms": p95_generation_time_ms,
        "high_confidence_override_rate": override_rate,
        "signal_false_positive_rate": false_positive_rate,
        "high_confidence_gate_total": high_total,
        "high_confidence_gate_overridden": high_overridden,
    }


__all__ = ["fetch_admin_metrics"]
