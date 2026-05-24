"""Opaque personalisation tokens — hashed instrument-id sets (P2-S9)."""

from __future__ import annotations

import hashlib
import hmac

TOKEN_PREFIX = "v1:"


def normalize_instrument_id(instrument_id: str) -> str:
    return instrument_id.strip().upper()


def instrument_digest(instrument_id: str, salt: str) -> str:
    """HMAC-SHA256 hex digest for one instrument id (matches client token derivation)."""
    key = salt.encode("utf-8")
    msg = normalize_instrument_id(instrument_id).encode("utf-8")
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


def parse_personalisation_token(token: str | None) -> frozenset[str]:
    """Return the set of instrument digests encoded in the token, or empty if invalid."""
    if not token or not token.startswith(TOKEN_PREFIX):
        return frozenset()
    body = token[len(TOKEN_PREFIX) :].strip()
    if not body:
        return frozenset()
    parts = [p for p in body.split(".") if p]
    return frozenset(parts)
