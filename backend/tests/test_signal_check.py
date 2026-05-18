"""Signal text vs macro fact evaluation — P1-S11."""

from datetime import UTC, datetime, timedelta

from app.services.signal_check import MarketFact, evaluate


def test_evaluate_triggered_with_recent_strong_overlap() -> None:
    ref = datetime(2026, 5, 18, 10, 0, tzinfo=UTC)
    phrase = (
        "india inflation outlook remains elevated across manufacturing sectors headline"
    )
    facts = [
        MarketFact("s1", phrase + " detail one", ref - timedelta(hours=1)),
        MarketFact("s2", phrase + " detail two", ref - timedelta(minutes=30)),
        MarketFact("s3", phrase + " detail three", ref - timedelta(minutes=10)),
    ]
    out = evaluate(phrase, facts, reference_time=ref)
    assert out.status == "triggered"
    assert len(out.direct_source_ids) == 3


def test_evaluate_partial_only_when_facts_stale() -> None:
    ref = datetime(2026, 5, 18, 10, 0, tzinfo=UTC)
    phrase = "reserve bank india policy guidance inflation corridor watch"
    facts = [
        MarketFact(
            "old",
            phrase + " markets",
            ref - timedelta(hours=10),
        )
    ]
    out = evaluate(phrase, facts, reference_time=ref)
    assert out.status == "partial"
    assert out.direct_source_ids == []


def test_evaluate_none_when_no_overlap() -> None:
    ref = datetime(2026, 5, 18, 10, 0, tzinfo=UTC)
    out = evaluate(
        "quantum computing patent litigation semiconductor fabs",
        [
            MarketFact("x", "wheat procurement msp hike rabi crop", ref),
        ],
        reference_time=ref,
    )
    assert out.status == "none"
