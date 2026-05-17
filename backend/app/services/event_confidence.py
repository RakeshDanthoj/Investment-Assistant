"""Heuristic 0–100 confidence for draft events before LLM ingest (PRD §7)."""

from __future__ import annotations

from app.sources.base import AdapterSource, RawEvent


def _joined_text(raw: RawEvent) -> str:
    chunks = [raw.title or ""]
    if raw.excerpt:
        chunks.append(raw.excerpt)
    return " ".join(chunks)


def infer_category_keyword_score(text: str) -> int:
    """Bounded lexical contribution (combined cap 22 pts)."""
    lower = text.lower()
    bumps: list[int] = []
    if any(
        needle in lower
        for needle in ("rbi", "repo rate", "monetary policy", "policy rate", "benchmark rate")
    ):
        bumps.append(22)
    if "sebi" in lower or "regulatory" in lower or "compliance" in lower:
        bumps.append(16)
    if "budget" in lower or "fiscal " in lower or "union cabinet" in lower:
        bumps.append(14)
    if "geopolit" in lower or "boundary" in lower or "border" in lower:
        bumps.append(10)
    if "sensex" in lower or "nifty " in lower or " inr " in lower or "rupee" in lower:
        bumps.append(12)
    if "india " in lower or lower.startswith("india"):
        bumps.append(6)
    return min(sum(sorted(bumps, reverse=True)[:2]), 22)


def score(source: AdapterSource, raw: RawEvent) -> int:
    """Combine source-tier prior + lexical signals; clamp to 0–100."""
    base_prior = {
        AdapterSource.RBI_RSS: 88,
        AdapterSource.NSE_BSE: 66,
        AdapterSource.NEWSAPI: 44,
    }[source]
    text_boost = infer_category_keyword_score(_joined_text(raw))
    jitter = hash(raw.canonical_url) % 3 if raw.canonical_url else 0
    total = base_prior + text_boost + jitter
    return max(0, min(total, 100))
