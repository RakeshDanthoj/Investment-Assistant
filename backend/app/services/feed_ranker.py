"""Re-rank Pulse feed cards by holdings token intersection (P2-S9)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from app.services.personalisation_token import parse_personalisation_token


def _intersection_count(card: dict[str, Any], token_hashes: frozenset[str], salt: str) -> int:
    from app.services.personalisation_token import instrument_digest

    instruments = card.get("instruments") or []
    if not isinstance(instruments, list) or not token_hashes:
        return 0
    count = 0
    seen: set[str] = set()
    for inst in instruments:
        if not isinstance(inst, dict):
            continue
        iid = inst.get("instrument_id")
        if not iid or not isinstance(iid, str):
            continue
        digest = instrument_digest(iid, salt)
        if digest in token_hashes and digest not in seen:
            seen.add(digest)
            count += 1
    return count


def _sort_key(card: dict[str, Any], token_hashes: frozenset[str], salt: str) -> tuple[int, float]:
    hits = _intersection_count(card, token_hashes, salt)
    created = card.get("created_at")
    ts = 0.0
    if isinstance(created, datetime):
        ts = created.timestamp()
    elif created is not None:
        try:
            ts = datetime.fromisoformat(str(created).replace("Z", "+00:00")).timestamp()
        except ValueError:
            ts = 0.0
    return (-hits, -ts)


def rerank(cards: list[dict[str, Any]], token: str | None, *, salt: str) -> list[dict[str, Any]]:
    """
    Stable re-order: cards with more instrument-assessment overlaps with the token
    float to the top; ties preserve relative order by recency (created_at desc).
    """
    token_hashes = parse_personalisation_token(token)
    if not token_hashes or not salt.strip():
        return cards
    indexed = list(enumerate(cards))
    indexed.sort(key=lambda pair: (_sort_key(pair[1], token_hashes, salt), pair[0]))
    return [card for _, card in indexed]
