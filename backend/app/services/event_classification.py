"""Map fetched raw headline text → PRD Tier-1 taxonomy (`event_category` enum)."""

from __future__ import annotations

from app.models.enums import EventCategory
from app.sources.base import AdapterSource, RawEvent


def _text(raw: RawEvent) -> str:
    merged = raw.title + " " + (raw.excerpt or "")
    return merged.lower()


def infer_event_category(source: AdapterSource, raw: RawEvent) -> EventCategory:
    t = _text(raw)
    if source == AdapterSource.RBI_RSS:
        return EventCategory.RBI_POLICY
    if source == AdapterSource.NSE_BSE:
        return EventCategory.INDIA_SPECIFIC
    # NewsAPI / misc
    if "budget" in t or "interim budget" in t or "finance bill" in t:
        return EventCategory.BUDGET
    if "rbi" in t or "repo" in t or "monetary policy" in t or "policy repo" in t:
        return EventCategory.RBI_POLICY
    if "sebi" in t or "regulatory" in t or "directive" in t:
        return EventCategory.REGULATORY
    if any(
        w in t
        for w in (
            "geopolitic",
            "border",
            "defence ",
            "defense ",
            "sanction",
            "conflict ",
        )
    ):
        return EventCategory.GEOPOLITICAL
    if "india" in t or "sensex" in t or "nifty" in t or "inr" in t or "mumbai" in t:
        return EventCategory.INDIA_SPECIFIC
    return EventCategory.MACRO
