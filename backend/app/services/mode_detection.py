"""Pure mode detection for onboarding — PRD §5 Screen 1 + P1-S2 routing rules."""

from __future__ import annotations

from typing import Literal

InvestmentStatus = Literal["starting_fresh", "has_investments", "curious"]
Horizon = Literal["under_1y", "1_3y", "3_7y", "7_plus"]
HorizonBucket = Literal["short", "mid", "long"]
UserMode = Literal["portfolio_builder", "portfolio_protector", "curious"]
StartingSurface = Literal["map", "pulse"]

# Map four discrete UI horizons onto three buckets so status × bucket = nine cases.
_BUCKET: dict[Horizon, HorizonBucket] = {
    "under_1y": "short",
    "1_3y": "short",
    "3_7y": "mid",
    "7_plus": "long",
}

# Nine explicit (status, horizon_bucket) rows — bucket only affects rationale copy.
_RATIONALE: dict[tuple[InvestmentStatus, HorizonBucket], str] = {
    ("curious", "short"): (
        "You're exploring how markets connect to everyday events — "
        "The Pulse will show you live implications without assuming a portfolio."
    ),
    ("curious", "mid"): (
        "You're curious with a multi-year lens — "
        "The Pulse keeps things event-led while you learn how sectors interact."
    ),
    ("curious", "long"): (
        "Long horizon, exploratory mindset — "
        "The Pulse keeps the feed contextual until you're ready to size positions."
    ),
    ("starting_fresh", "short"): (
        "You're new to investing on a nearer horizon — "
        "The Map builds sector literacy before headline events feel actionable."
    ),
    ("starting_fresh", "mid"): (
        "Starting out with years to compound — "
        "The Map grounds you in how sectors work before the live feed."
    ),
    ("starting_fresh", "long"): (
        "Building from scratch across a long horizon — "
        "The Map is your preparation layer so later newsfeeds stay interpretable."
    ),
    ("has_investments", "short"): (
        "You hold positions and track a shorter window — "
        "The Pulse surfaces what may affect what you own, right now."
    ),
    ("has_investments", "mid"): (
        "Invested across a few cycles — "
        "The Pulse matches how you experience markets: implications first."
    ),
    ("has_investments", "long"): (
        "Long-term owner with live allocations — "
        "The Pulse is the right home screen for what moves your book today."
    ),
}


def horizon_bucket(horizon: Horizon) -> HorizonBucket:
    return _BUCKET[horizon]


def detect_mode(
    status: InvestmentStatus, horizon: Horizon
) -> tuple[UserMode, StartingSurface, str]:
    """
    Map investment posture + horizon to user mode, first surface, and one-sentence rationale.

    Routing (P1-S2 acceptance):
    - portfolio_builder → /map
    - portfolio_protector | curious → /pulse
    """
    bucket = horizon_bucket(horizon)
    rationale = _RATIONALE[status, bucket]
    if status == "curious":
        return ("curious", "pulse", rationale)
    if status == "starting_fresh":
        return ("portfolio_builder", "map", rationale)
    return ("portfolio_protector", "pulse", rationale)
