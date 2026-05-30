"""Factor DB keyword match for events (P3-S1g / PRD2 §3.1)."""

from __future__ import annotations

import re
from functools import lru_cache

from app.models.enums import EventCategory

_FACTOR_KEYWORDS: dict[str, tuple[str, ...]] = {
    "crude_oil": ("crude", "oil", "opec", "brent", "wti", "petroleum"),
    "dollar_rupee": ("inr", "rupee", "usd", "dollar", "forex", "fx", "per usd"),
    "domestic_interest_rates": (
        "rbi",
        "repo",
        "mpc",
        "rate cut",
        "rate hold",
        "monetary policy",
        "liquidity injection",
        "policy rate",
    ),
    "global_risk_sentiment": (
        "fii",
        "risk premium",
        "vix",
        "selloff",
        "outflow",
        "safe-haven",
        "geopolitical",
        "tariff",
        "tensions",
    ),
    "monsoon_index": ("monsoon", "rainfall", "imd", "kerala onset"),
    "government_capex": ("budget", "capex", "pli", "fiscal", "union budget", "deficit"),
    "gst_collections_trend": ("gst", "tax collection"),
    "sector_regulatory_environment": (
        "sebi",
        "regulatory",
        "usfda",
        "compliance",
        "nse",
        "f&o",
        "circuit",
        "observations",
    ),
}

_CATEGORY_DEFAULT_FACTORS: dict[EventCategory, tuple[str, ...]] = {
    EventCategory.RBI_POLICY: ("domestic_interest_rates", "sector_regulatory_environment"),
    EventCategory.BUDGET: ("government_capex", "gst_collections_trend"),
    EventCategory.GEOPOLITICAL: ("global_risk_sentiment", "dollar_rupee"),
    EventCategory.MACRO: ("dollar_rupee", "global_risk_sentiment"),
    EventCategory.REGULATORY: ("sector_regulatory_environment",),
    EventCategory.INDIA_SPECIFIC: ("global_risk_sentiment", "domestic_interest_rates"),
}


def _normalise_text(*parts: str | None) -> str:
    joined = " ".join(p for p in parts if p).lower()
    return re.sub(r"\s+", " ", joined)


@lru_cache(maxsize=1)
def all_factor_slugs() -> tuple[str, ...]:
    return tuple(_FACTOR_KEYWORDS.keys())


def matched_factor_slugs(
    *,
    title: str,
    body: str | None,
    category: str | EventCategory,
) -> list[str]:
    """Return distinct factor slugs with keyword hits (order stable)."""
    cat = EventCategory(category) if isinstance(category, str) else category
    haystack = _normalise_text(title, body)
    hits: list[str] = []
    for slug, keywords in _FACTOR_KEYWORDS.items():
        if any(kw in haystack for kw in keywords):
            hits.append(slug)
    if not hits:
        for slug in _CATEGORY_DEFAULT_FACTORS.get(cat, ()):
            if slug not in hits:
                hits.append(slug)
    return hits


def match_strength(*, factor_match_count: int, keyword_hit_count: int) -> float:
    """
    PRD2 match strength from factor touch count.

    Direct keyword hits to 2+ factors → 1.0; 1 factor → 0.7; category-only → 0.4; none → 0.0.
    """
    if keyword_hit_count >= 2:
        return 1.0
    if keyword_hit_count == 1:
        return 0.7
    if factor_match_count >= 1:
        return 0.4
    return 0.0


def count_keyword_matched_factors(
    *,
    title: str,
    body: str | None,
) -> int:
    haystack = _normalise_text(title, body)
    return sum(
        1 for keywords in _FACTOR_KEYWORDS.values() if any(kw in haystack for kw in keywords)
    )


def compute_factor_match(
    *,
    title: str,
    body: str | None,
    category: str | EventCategory,
) -> tuple[float, int, list[str]]:
    """Return (match_strength, factor_db_match_count, matched_slugs)."""
    keyword_hits = count_keyword_matched_factors(title=title, body=body)
    slugs = matched_factor_slugs(title=title, body=body, category=category)
    count = len(slugs)
    strength = match_strength(factor_match_count=count, keyword_hit_count=keyword_hits)
    return strength, count, slugs
