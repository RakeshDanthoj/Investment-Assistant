"""Ensure Insight/Context numerics appear in the Evidence corpus (PRD §6.3)."""

from __future__ import annotations

import re

# Currency, percentages, and standalone numeric tokens (conservative).
_NUMERIC_TOKEN = re.compile(
    r"(?:₹|Rs\.?|INR)\s*[\d,]+(?:\.\d+)?|\d[\d,]*(?:\.\d+)?%|(?<!\w)\d[\d,]*(?:\.\d+)?(?!\w)",
    re.IGNORECASE,
)


def normalize_numeric_token(raw: str) -> str:
    s = raw.strip()
    s = s.replace(",", "")
    s = re.sub(r"^(?:₹|Rs\.?|INR)\s*", "", s, flags=re.IGNORECASE)
    return s.strip().lower()


def extract_numeric_tokens(text: str) -> list[str]:
    return [normalize_numeric_token(m.group(0)) for m in _NUMERIC_TOKEN.finditer(text)]


def validate_numbers_in_evidence(*, prose: str, evidence_corpus: str) -> None:
    """
    Raises ValueError listing the first offending token not found in evidence_corpus
    (after normalising commas; case-insensitive substring match on corpus).
    """
    corpus_norm = evidence_corpus.replace(",", "").lower()
    seen: set[str] = set()
    for token in extract_numeric_tokens(prose):
        if token in seen:
            continue
        seen.add(token)
        if token not in corpus_norm:
            raise ValueError(f"numeric token not grounded in evidence: {token!r}")
