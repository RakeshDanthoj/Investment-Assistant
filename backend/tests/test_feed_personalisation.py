"""Feed personalisation token re-rank (P2-S9)."""

from datetime import UTC, datetime

from app.services.feed_ranker import rerank
from app.services.personalisation_token import instrument_digest


def _token_for(*instrument_ids: str, salt: str = "test-salt") -> str:
    digests = sorted(instrument_digest(i, salt) for i in instrument_ids)
    return "v1:" + ".".join(digests)


def test_rerank_promotes_cards_with_holding_intersection() -> None:
    salt = "test-salt"
    now = datetime.now(tz=UTC)
    cards = [
        {
            "id": "a",
            "created_at": now,
            "instruments": [{"instrument_id": "RELIANCE", "signal_type": "watch"}],
        },
        {
            "id": "b",
            "created_at": now,
            "instruments": [{"instrument_id": "HDFCBANK", "signal_type": "headwind"}],
        },
        {
            "id": "c",
            "created_at": now,
            "instruments": [],
        },
    ]
    token = _token_for("HDFCBANK", salt=salt)
    out = rerank(cards, token, salt=salt)
    assert [c["id"] for c in out] == ["b", "a", "c"]


def test_rerank_noop_without_token() -> None:
    cards = [{"id": "x", "instruments": [], "created_at": None}]
    assert rerank(cards, None, salt="salt") == cards
    assert rerank(cards, "", salt="salt") == cards


def test_rerank_noop_with_empty_salt() -> None:
    cards = [{"id": "x", "instruments": [{"instrument_id": "TCS"}], "created_at": None}]
    token = _token_for("TCS")
    assert rerank(cards, token, salt="") == cards
