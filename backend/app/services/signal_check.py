"""Per-signal evaluation vs market/macro facts (P1-S11)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Literal


@dataclass(frozen=True)
class MarketFact:
    """One corroborating row from market or macro ingest (events feed, future price feeds, etc.)."""

    source_id: str
    summary: str
    observed_at: datetime

    def __post_init__(self) -> None:
        if self.observed_at.tzinfo is None:
            object.__setattr__(self, "observed_at", self.observed_at.replace(tzinfo=UTC))


def _tokens(text: str) -> set[str]:
    return {t for t in re.findall(r"[a-z0-9]{3,}", text.lower()) if len(t) >= 3}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


@dataclass
class SignalEvalResult:
    """Result of comparing a signal to available facts."""

    direct_source_ids: list[str] = field(default_factory=list)
    partial_source_ids: list[str] = field(default_factory=list)

    @property
    def status(self) -> Literal["triggered", "partial", "none"]:
        if self.direct_source_ids:
            return "triggered"
        if self.partial_source_ids:
            return "partial"
        return "none"


def evaluate(
    signal_text: str,
    facts: list[MarketFact],
    *,
    reference_time: datetime | None = None,
    direct_window: timedelta = timedelta(hours=4),
    direct_jaccard_min: float = 0.28,
    partial_jaccard_min: float = 0.12,
) -> SignalEvalResult:
    """
    Classify corroboration for one signal.

    * **direct** — strong lexical overlap with a fact observed within ``direct_window``
      of ``reference_time``.
    * **partial** — weaker overlap, or strong overlap outside the direct window.
    """
    ref = reference_time or datetime.now(tz=UTC)
    if ref.tzinfo is None:
        ref = ref.replace(tzinfo=UTC)

    sig_tokens = _tokens(signal_text)
    if not sig_tokens:
        return SignalEvalResult()

    direct_ids: set[str] = set()
    partial_ids: set[str] = set()

    for fact in facts:
        fact_tokens = _tokens(fact.summary)
        score = _jaccard(sig_tokens, fact_tokens)
        if score < partial_jaccard_min:
            continue
        obs = fact.observed_at if fact.observed_at.tzinfo else fact.observed_at.replace(tzinfo=UTC)
        age = abs((ref - obs).total_seconds())
        is_recent = age <= direct_window.total_seconds()
        if score >= direct_jaccard_min and is_recent:
            direct_ids.add(fact.source_id)
        else:
            partial_ids.add(fact.source_id)

    partial_ids -= direct_ids
    return SignalEvalResult(
        direct_source_ids=sorted(direct_ids),
        partial_source_ids=sorted(partial_ids),
    )
