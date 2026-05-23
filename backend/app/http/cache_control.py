"""Cache-Control headers for published read paths (P1.5-S4)."""

from __future__ import annotations

PUBLISHED_READ_CACHE = "private, max-age=60, stale-while-revalidate=300"
NO_STORE_CACHE = "no-store"

CACHEABLE_LIFECYCLE_STATES: frozenset[str] = frozenset(
    {
        "published",
        "active",
        "signal_triggered",
        "thesis_confirmed",
        "thesis_weakened",
        "resolved",
    }
)


def cache_control_for_lifecycle(lifecycle_state: str | None) -> str:
    if lifecycle_state and lifecycle_state.strip().lower() in CACHEABLE_LIFECYCLE_STATES:
        return PUBLISHED_READ_CACHE
    return NO_STORE_CACHE


def cache_control_for_feed() -> str:
    """Pulse feed only surfaces published lifecycle cards."""
    return PUBLISHED_READ_CACHE


def cache_control_for_card_detail(*, view: str, lifecycle_state: str | None) -> str:
    if view == "original":
        return PUBLISHED_READ_CACHE
    return cache_control_for_lifecycle(lifecycle_state)
