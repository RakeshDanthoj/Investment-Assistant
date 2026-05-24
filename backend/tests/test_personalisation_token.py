"""Personalisation token parse + digest (P2-S9)."""

from app.services.personalisation_token import (
    instrument_digest,
    parse_personalisation_token,
)


def test_parse_token_extracts_digest_set() -> None:
    d1 = instrument_digest("HDFCBANK", "salt")
    d2 = instrument_digest("TCS", "salt")
    token = f"v1:{d2}.{d1}"
    assert parse_personalisation_token(token) == frozenset({d1, d2})


def test_parse_invalid_token_returns_empty() -> None:
    assert parse_personalisation_token(None) == frozenset()
    assert parse_personalisation_token("") == frozenset()
    assert parse_personalisation_token("v2:abc") == frozenset()
