"""P3-T3: Confidence scoring verification gate (G-01, G-02).

Proves breakdown API, FoW dampener, and signal monitor agree on rule-based tiers
before editorial hard gates (P3-S1i) depend on scores.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.confidence_config import FOG_DAMPENER, THRESHOLDS, WEIGHTS
from app.db.migrate import apply_migrations
from app.main import app
from app.models.enums import LifecycleState, SignalState
from app.services.confidence_gate import route
from app.services.confidence_scorer import tier_from_score
from app.services.signal_check import MarketFact
from app.services.signal_monitor_runner import run_signal_monitor


@pytest.fixture(scope="module", autouse=True)
def ensure_migrations(db_connection):
    apply_migrations(db_connection)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _weighted_sum_from_breakdown(body: dict) -> float:
    inputs = body["inputs"]
    total = sum(float(inputs[key]["value"]) * WEIGHTS[key] for key in WEIGHTS)
    return round(min(max(total, 0.0), 1.0), 3)


def test_confidence_breakdown_weighted_sum_matches_raw(
    client: TestClient, db_connection
) -> None:
    """Breakdown input bars must reconstruct API confidence_raw within epsilon."""
    event_id = uuid4()
    canon = f"pytest:confidence-sum:{uuid4()}@invalid"
    ref = datetime(2025, 6, 1, 10, 0, tzinfo=UTC)
    sources = [
        {
            "event_source": "rbi_rss",
            "canonical_url": "https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx",
            "retrieved_at": ref.isoformat(),
        },
        {
            "event_source": "newsapi",
            "canonical_url": "https://economictimes.indiatimes.com/markets/story",
            "retrieved_at": ref.isoformat(),
        },
        {
            "event_source": "newsapi",
            "canonical_url": "https://livemint.com/markets/story",
            "retrieved_at": ref.isoformat(),
        },
    ]
    try:
        with db_connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.events (
                  id, title, category, confidence_score, lifecycle_state,
                  canonical_url, event_source, source_count, sources,
                  confidence_raw, confidence_effective, factor_db_match_count,
                  created_at
                )
                VALUES (
                  %s, %s, 'rbi_policy'::event_category, 88, 'draft',
                  %s, 'rbi_rss', 3, %s::jsonb,
                  0.0, 0.0, 2, %s
                )
                """,
                (
                    str(event_id),
                    "RBI MPC repo unchanged — pytest sum gate",
                    canon,
                    json.dumps(sources),
                    ref,
                ),
            )
        db_connection.commit()

        resp = client.get(f"/api/events/{event_id}/confidence-breakdown")
        assert resp.status_code == 200
        body = resp.json()
        recomputed = _weighted_sum_from_breakdown(body)
        assert body["confidence_raw"] == pytest.approx(recomputed, abs=0.002)
    finally:
        with db_connection.cursor() as cur:
            cur.execute("DELETE FROM public.events WHERE id = %s", (str(event_id),))
        db_connection.commit()


def test_confidence_breakdown_fow_dampens_effective_and_tier(
    client: TestClient, db_connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When FoW is active, effective = raw × 0.6 and tier follows effective score."""
    monkeypatch.setattr(
        "app.services.confidence_scorer.fetch_fog_active",
        lambda **_kwargs: True,
    )
    subject_id = uuid4()
    canon = f"pytest:confidence-fow:{uuid4()}@invalid"
    ref = datetime(2025, 6, 1, 12, 0, tzinfo=UTC)
    sources = [
        {
            "event_source": "rbi_rss",
            "canonical_url": "https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx",
            "retrieved_at": ref.isoformat(),
        },
        {
            "event_source": "newsapi",
            "canonical_url": "https://economictimes.indiatimes.com/markets/story",
            "retrieved_at": ref.isoformat(),
        },
        {
            "event_source": "newsapi",
            "canonical_url": "https://livemint.com/markets/story",
            "retrieved_at": ref.isoformat(),
        },
    ]
    try:
        with db_connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.events (
                  id, title, category, confidence_score, lifecycle_state,
                  canonical_url, event_source, source_count, sources,
                  confidence_raw, confidence_effective, factor_db_match_count,
                  created_at
                )
                VALUES (
                  %s, %s, 'rbi_policy'::event_category, 88, 'draft',
                  %s, 'rbi_rss', 3, %s::jsonb,
                  0.0, 0.0, 2, %s
                )
                """,
                (
                    str(subject_id),
                    "RBI policy headline — pytest FoW gate",
                    canon,
                    json.dumps(sources),
                    ref,
                ),
            )
        db_connection.commit()

        resp = client.get(f"/api/events/{subject_id}/confidence-breakdown")
        assert resp.status_code == 200
        body = resp.json()
        assert body["fog_active"] is True
        assert body["fog_dampener"] == pytest.approx(FOG_DAMPENER)
        assert body["confidence_effective"] == pytest.approx(
            round(body["confidence_raw"] * FOG_DAMPENER, 3), abs=0.002
        )
        assert body["tier"] == tier_from_score(body["confidence_effective"])
        assert route(body["confidence_effective"]).tier == body["tier"]
    finally:
        with db_connection.cursor() as cur:
            cur.execute("DELETE FROM public.events WHERE id = %s", (str(subject_id),))
        db_connection.commit()


def test_signal_monitor_routes_by_effective_score_not_fact_count(
    db_connection,
) -> None:
    """Regression: three matching facts no longer imply high gate without effective score."""
    event_id = uuid4()
    card_id = uuid4()
    signal_id = uuid4()
    canon = f"pytest:{uuid4()}@signal.invalid"
    ref = datetime(2026, 5, 18, 10, 30, tzinfo=UTC)
    phrase = (
        "india inflation outlook remains elevated across manufacturing sectors "
        f"headline pytest signalid {signal_id}"
    )
    facts = [
        MarketFact(
            f"src{i}",
            phrase + f" wire {i}",
            ref - timedelta(minutes=i),
        )
        for i in range(3)
    ]
    confidence_effective = 0.40

    try:
        with db_connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.events (
                  id, title, category, confidence_score, lifecycle_state,
                  canonical_url, event_source, confidence_raw, confidence_effective
                )
                VALUES (%s, %s, 'macro'::event_category, 60, 'published',
                  %s, 'pytest', 0.80, %s)
                """,
                (
                    str(event_id),
                    "Signal monitor effective-score regression",
                    canon,
                    confidence_effective,
                ),
            )
            cur.execute(
                """
                INSERT INTO public.cards (
                  id, event_id, title, insight_layer, context_layer, evidence_layer,
                  dissenting_view, framework_behind_this, prompt_version, lifecycle_state
                )
                VALUES (
                  %s, %s, 'Signal card', 'Insight [MEASURED]', 'Ctx [MEASURED]',
                  '{}'::jsonb, 'Dissent [MEASURED]', 'Fw [MEASURED]', 'pytest', %s
                )
                """,
                (str(card_id), str(event_id), LifecycleState.PUBLISHED.value),
            )
            cur.execute(
                """
                INSERT INTO public.signals (id, card_id, signal_text, state)
                VALUES (%s, %s, %s, %s)
                """,
                (str(signal_id), str(card_id), phrase, SignalState.PENDING.value),
            )
        db_connection.commit()

        assert route(confidence_effective).tier == "low"
        assert route(confidence_effective).tier != route(THRESHOLDS["high"]).tier

        summary = run_signal_monitor(
            reference_time=ref,
            skip_market_hours_check=True,
            facts_provider=lambda _rt: facts,
            emit_notifications=False,
            only_card_id=card_id,
        )
        assert summary.skipped_no_db is False
        assert summary.low_actions >= 1

        with db_connection.cursor() as cur:
            cur.execute(
                """
                SELECT gate FROM public.confidence_gate_log
                WHERE signal_id = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (str(signal_id),),
            )
            row = cur.fetchone()
            assert row is not None
            assert row[0] == "low"
            cur.execute(
                "SELECT 1 FROM public.digest_log WHERE signal_id = %s",
                (str(signal_id),),
            )
            assert cur.fetchone() is not None
    finally:
        with db_connection.cursor() as cur:
            cur.execute("DELETE FROM public.digest_log WHERE signal_id = %s", (str(signal_id),))
            cur.execute("DELETE FROM public.cards WHERE id = %s", (str(card_id),))
            cur.execute("DELETE FROM public.events WHERE id = %s", (str(event_id),))
        db_connection.commit()
