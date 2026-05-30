"""High / Medium / Low routing from rule-based confidence scores (P3-S1g / G-02)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.core.confidence_config import THRESHOLDS

GateTier = Literal["high", "medium", "low"]


@dataclass(frozen=True)
class GateDecision:
    tier: GateTier
    reason: str


def route(confidence_effective: float) -> GateDecision:
    """
    Route editorial/signal actions from ``confidence_effective`` (0–1).

    * **high** — effective ≥ 0.75
    * **medium** — 0.55–0.74 (narrow band per PO G-02)
    * **low** — < 0.55
    """
    score = float(confidence_effective)
    if score >= THRESHOLDS["high"]:
        return GateDecision("high", "score_gte_075")
    if score >= THRESHOLDS["medium_low"]:
        return GateDecision("medium", "score_055_074")
    return GateDecision("low", "score_lt_055")
