"""Round-robin factor selection for NewsAPI polls (P3-S1d)."""

from __future__ import annotations

from app.services.newsapi_config import NewsApiSchedulerConfig, load_newsapi_config

PollStatus = str  # ok | empty | error


def pick_next_factor_slug(
    *,
    factor_order: tuple[str, ...],
    last_polled_slug: str | None,
    counts_today: dict[str, int],
    daily_budgets: dict[str, int],
) -> str | None:
    """
    Return the next factor slug with remaining daily budget.

    Rotates forward from ``last_polled_slug`` (exclusive); scans at most one full cycle.
    """
    if not factor_order:
        return None

    start = 0
    if last_polled_slug and last_polled_slug in factor_order:
        start = (factor_order.index(last_polled_slug) + 1) % len(factor_order)

    for offset in range(len(factor_order)):
        slug = factor_order[(start + offset) % len(factor_order)]
        used = counts_today.get(slug, 0)
        budget = daily_budgets.get(slug, 0)
        if used < budget:
            return slug
    return None


def resolve_next_factor(
    *,
    last_polled_slug: str | None,
    counts_today: dict[str, int],
    config: NewsApiSchedulerConfig | None = None,
) -> str | None:
    cfg = config or load_newsapi_config()
    if cfg.mode != "round_robin":
        raise ValueError(f"unsupported scheduler mode: {cfg.mode}")
    return pick_next_factor_slug(
        factor_order=cfg.factor_order,
        last_polled_slug=last_polled_slug,
        counts_today=counts_today,
        daily_budgets=cfg.daily_budgets,
    )
