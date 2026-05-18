"""LLM card-generation daily ceiling (50/day UTC, PRD §12 risk 7)."""

from __future__ import annotations

import logging
from typing import Any

from psycopg.rows import dict_row

from app.db.connection import connection

_LOG = logging.getLogger(__name__)

_DAILY_CAP = 50


class DailyLLMCardCapError(RuntimeError):
    """Raised when the UTC daily generation budget is exhausted."""


def try_consume_slot(*, max_cards_per_day: int = _DAILY_CAP) -> bool:
    """
    Atomically consume one slot if below the cap.
    Returns True if a slot was consumed, False if at cap (see consume_slot_or_raise).
    """
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute("SELECT public.try_consume_llm_card_slot(%s) AS ok", (max_cards_per_day,))
        row = cur.fetchone()
    ok = bool(row and row.get("ok"))
    _LOG.info("cost_guard.try_consume", extra={"ok": ok, "cap": max_cards_per_day})
    return ok


def consume_slot_or_raise(*, max_cards_per_day: int = _DAILY_CAP) -> None:
    if not try_consume_slot(max_cards_per_day=max_cards_per_day):
        raise DailyLLMCardCapError(f"daily LLM card cap reached ({max_cards_per_day} UTC)")


def estimate_cost_usd(*, input_tokens: int, output_tokens: int) -> float:
    """
    Rough Gemini Flash–class pricing for dashboarding (not invoicing).
    Override with env-driven table later; keeps per-card field populated.
    """
    # USD per million tokens — approximate public Gemini Flash tier (research estimate).
    in_rate = 0.10 / 1_000_000
    out_rate = 0.40 / 1_000_000
    return round(input_tokens * in_rate + output_tokens * out_rate, 6)


def merge_usage(acc: dict[str, Any], usage: dict[str, int]) -> None:
    acc["input_tokens"] = int(acc.get("input_tokens", 0)) + int(usage.get("input_tokens", 0))
    acc["output_tokens"] = int(acc.get("output_tokens", 0)) + int(
        usage.get("output_tokens", 0)
    )
