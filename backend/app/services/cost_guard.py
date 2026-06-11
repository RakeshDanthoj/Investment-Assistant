"""LLM card-generation daily ceiling + monthly INR budget guard (P1-S7, P2-S13)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from psycopg.rows import dict_row

from app.core.settings import get_settings
from app.db.connection import connection

_LOG = logging.getLogger(__name__)

_DAILY_CAP = 50

# Rough average tokens per 3-call ICE draft (synthesis + dissent + framework).
_ESTIMATED_DRAFT_INPUT_TOKENS = 12_000
_ESTIMATED_DRAFT_OUTPUT_TOKENS = 4_000


class DailyLLMCardCapError(RuntimeError):
    """Raised when the UTC daily generation budget is exhausted."""


class MonthlyLLMBudgetError(RuntimeError):
    """Raised when projected month LLM spend would exceed the configured INR ceiling."""


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
    Rough Nemotron 3 Ultra pricing for dashboarding (not invoicing).
    Override with env-driven table later; keeps per-card field populated.
    """
    in_rate = 0.50 / 1_000_000
    out_rate = 2.50 / 1_000_000
    return round(input_tokens * in_rate + output_tokens * out_rate, 6)


def merge_usage(acc: dict[str, Any], usage: dict[str, int]) -> None:
    acc["input_tokens"] = int(acc.get("input_tokens", 0)) + int(usage.get("input_tokens", 0))
    acc["output_tokens"] = int(acc.get("output_tokens", 0)) + int(
        usage.get("output_tokens", 0)
    )


def month_to_date_spend_usd() -> float:
    """Sum recorded llm_cost_usd on cards created in the current UTC month."""
    month_start = datetime.now(tz=UTC).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT COALESCE(SUM(llm_cost_usd), 0)::float AS total
            FROM public.cards
            WHERE created_at >= %s
            """,
            (month_start,),
        )
        row = cur.fetchone()
    return float(row["total"]) if row else 0.0


def projected_month_spend_inr(*, additional_usd: float = 0.0) -> Decimal:
    """Month-to-date USD spend + optional increment, converted to INR."""
    settings = get_settings()
    mtd_usd = Decimal(str(month_to_date_spend_usd())) + Decimal(str(additional_usd))
    rate = Decimal(str(settings.usd_inr_rate))
    return (mtd_usd * rate).quantize(Decimal("0.01"))


def check_monthly_budget_or_raise(*, additional_usd: float | None = None) -> None:
    """
    Abort pipeline when projected month spend exceeds the configured INR budget.
    Uses rolling token spend on cards plus an optional estimate for the pending run.
    """
    settings = get_settings()
    budget_inr = Decimal(str(settings.llm_monthly_budget_inr))
    if budget_inr <= 0:
        return

    if additional_usd is None:
        additional_usd = estimate_cost_usd(
            input_tokens=_ESTIMATED_DRAFT_INPUT_TOKENS,
            output_tokens=_ESTIMATED_DRAFT_OUTPUT_TOKENS,
        )

    projected = projected_month_spend_inr(additional_usd=additional_usd)
    if projected > budget_inr:
        raise MonthlyLLMBudgetError(
            f"monthly LLM budget exceeded: projected ₹{projected} > ceiling ₹{budget_inr}"
        )

    _LOG.info(
        "cost_guard.monthly_ok",
        extra={
            "projected_inr": str(projected),
            "budget_inr": str(budget_inr),
            "additional_usd": additional_usd,
        },
    )


__all__ = [
    "DailyLLMCardCapError",
    "MonthlyLLMBudgetError",
    "check_monthly_budget_or_raise",
    "consume_slot_or_raise",
    "estimate_cost_usd",
    "merge_usage",
    "month_to_date_spend_usd",
    "projected_month_spend_inr",
    "try_consume_slot",
]
