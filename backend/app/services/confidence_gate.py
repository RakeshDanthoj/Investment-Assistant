"""High / Medium / Low confidence routing for signal hits (PRD §6.4, P1-S11)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.services.signal_check import SignalEvalResult

GateTier = Literal["high", "medium", "low"]


@dataclass(frozen=True)
class GateDecision:
    tier: GateTier
    reason: str


def route(result: SignalEvalResult) -> GateDecision:
    """
    * **high** — 3+ independent direct corroborations (within the evaluator's recency window).
    * **medium** — 1–2 direct hits, or 1–2 partial-only hits.
    * **low** — additional corroboration that does not meet editorial auto-queue bar.

    Call only when :func:`app.services.signal_check.evaluate` returned a non-``none`` status.
    """
    d = len(result.direct_source_ids)
    p = len(result.partial_source_ids)

    if d == 0 and p == 0:
        raise ValueError("route() called with empty evaluation — check status != 'none' first")

    if d >= 3:
        return GateDecision(
            "high",
            f"three_plus_direct_sources:{d}",
        )

    if 1 <= d <= 2:
        return GateDecision(
            "medium",
            f"one_to_two_direct_sources:{d}",
        )

    if d == 0 and 1 <= p <= 2:
        return GateDecision(
            "medium",
            f"partial_match_only_sources:{p}",
        )

    return GateDecision(
        "low",
        f"weak_or_diffuse_corroboration_direct_{d}_partial_{p}",
    )
