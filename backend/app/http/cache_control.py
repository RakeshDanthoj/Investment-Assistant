"""Cache-Control headers for published read paths (P1.5-S4)."""

from __future__ import annotations

PUBLISHED_READ_CACHE = "private, max-age=60, stale-while-revalidate=300"
PUBLIC_FEED_CACHE = "public, max-age=60, stale-while-revalidate=300"
MAP_READ_CACHE = "private, max-age=300, stale-while-revalidate=600"
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


def cache_control_for_feed(
    *,
    session_id: object | None = None,
    personalisation_token: str | None = None,
) -> str:
    """Public edge cache when anonymous; private when session or holdings token present."""
    has_session = session_id is not None
    has_token = bool(personalisation_token and personalisation_token.strip())
    if has_session or has_token:
        return PUBLISHED_READ_CACHE
    return PUBLIC_FEED_CACHE


def cache_control_for_map_read() -> str:
    """The Map sector summary and matrix read paths (PI-S1 / D9)."""
    return MAP_READ_CACHE


def cache_control_for_card_detail(*, view: str, lifecycle_state: str | None) -> str:
    if view == "original":
        return PUBLISHED_READ_CACHE
    return cache_control_for_lifecycle(lifecycle_state)
