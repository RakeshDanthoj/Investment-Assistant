"""Merged market facts for signal monitor — P2-S14."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from app.core.settings import Settings
from app.services.market_facts import build_market_facts, fetch_recent_event_facts
from app.services.market_facts_adapters import merge_market_facts
from app.services.signal_check import MarketFact, evaluate


def test_merge_dedup_keeps_newest_observed_at() -> None:
    t_old = datetime(2026, 5, 24, 8, 0, tzinfo=UTC)
    t_new = datetime(2026, 5, 24, 9, 0, tzinfo=UTC)
    stream_a = [
        MarketFact("dup:1", "alpha markets inflation", t_old),
        MarketFact("unique:a", "beta sector", t_new),
    ]
    stream_b = [
        MarketFact("dup:1", "alpha markets inflation updated", t_new),
    ]
    merged = merge_market_facts(stream_a, stream_b, max_total=10)
    by_id = {f.source_id: f for f in merged}
    assert by_id["dup:1"].summary.endswith("updated")
    assert by_id["dup:1"].observed_at == t_new
    assert merged[0].observed_at >= merged[-1].observed_at


def test_merge_caps_total() -> None:
    base = datetime(2026, 5, 24, 10, 0, tzinfo=UTC)
    facts = [
        MarketFact(f"id:{i}", f"headline number {i} macro", base - timedelta(minutes=i))
        for i in range(20)
    ]
    capped = merge_market_facts(facts, max_total=5)
    assert len(capped) == 5


def test_evaluate_sees_facts_from_events_and_nse_streams() -> None:
    ref = datetime(2026, 5, 24, 10, 0, tzinfo=UTC)
    phrase = (
        "acme bank board meeting dividend guidance india manufacturing outlook headline"
    )
    event_fact = MarketFact(
        "event:evt-1",
        phrase + " editorial event line",
        ref - timedelta(hours=1),
    )
    nse_fact = MarketFact(
        "nse:abc123",
        "ACME BANK: " + phrase + " corporate filing",
        ref - timedelta(minutes=20),
    )
    out = evaluate(phrase, [event_fact, nse_fact], reference_time=ref)
    assert out.status == "triggered"
    assert "event:evt-1" in out.direct_source_ids
    assert any(sid.startswith("nse:") for sid in out.direct_source_ids)


@patch("app.services.market_facts.collect_market_stream_facts")
@patch("app.services.market_facts.fetch_recent_event_facts")
def test_build_market_facts_merges_enabled_streams(
    mock_events: MagicMock,
    mock_collect: MagicMock,
) -> None:
    ref = datetime(2026, 5, 24, 12, 0, tzinfo=UTC)
    events = [MarketFact("event:1", "rbi policy rate corridor", ref)]
    nse = [MarketFact("nse:1", "NIFTY issuer board meeting", ref)]
    mock_events.return_value = events
    mock_collect.return_value = [events, nse]

    settings = Settings(
        signal_facts_events_enabled=True,
        signal_facts_nse_enabled=True,
        signal_facts_index_enabled=False,
        signal_facts_max_total=50,
    )
    merged = build_market_facts(reference_time=ref, settings=settings)
    assert len(merged) == 2
    ids = {f.source_id for f in merged}
    assert "event:1" in ids
    assert "nse:1" in ids
    mock_collect.assert_called_once()


def test_fetch_recent_event_facts_prefixes_source_id() -> None:
    ref = datetime(2026, 5, 24, 12, 0, tzinfo=UTC)
    row = {
        "source_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
        "title": "India CPI print",
        "created_at": ref,
    }

    class FakeCursor:
        def execute(self, *_args: object, **_kwargs: object) -> None:
            return None

        def fetchall(self) -> list[dict]:
            return [row]

        def __enter__(self) -> FakeCursor:
            return self

        def __exit__(self, *_args: object) -> bool:
            return False

    class FakeConn:
        def cursor(self, **_kwargs: object) -> FakeCursor:
            return FakeCursor()

        def __enter__(self) -> FakeConn:
            return self

        def __exit__(self, *_args: object) -> bool:
            return False

    with patch("app.services.market_facts.connection", return_value=FakeConn()):
        facts = fetch_recent_event_facts(reference_time=ref)
    assert facts[0].source_id.startswith("event:")
