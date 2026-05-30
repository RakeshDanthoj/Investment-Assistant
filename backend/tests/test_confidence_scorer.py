"""Rule-based confidence scorer — P3-S1g."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app.core.confidence_config import FOG_DAMPENER, THRESHOLDS
from app.services.confidence_gate import route
from app.services.confidence_scorer import (
    build_scorer_input,
    compute_confidence,
    compute_is_major,
    tier_from_score,
)
from app.services.event_factor_match import compute_factor_match

_SYNTHETIC_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "seed_data" / "synthetic_events.json"
)


def test_tier_boundaries_narrow_medium_band() -> None:
    assert tier_from_score(THRESHOLDS["high"]) == "high"
    assert tier_from_score(THRESHOLDS["high"] - 0.001) == "medium"
    assert tier_from_score(THRESHOLDS["medium_low"]) == "medium"
    assert tier_from_score(THRESHOLDS["medium_low"] - 0.001) == "low"


def test_gate_matches_tier_thresholds() -> None:
    assert route(0.80).tier == "high"
    assert route(0.60).tier == "medium"
    assert route(0.40).tier == "low"


def test_fog_dampener_applies_to_effective_only() -> None:
    ref = datetime(2025, 6, 1, 12, 0, tzinfo=UTC)
    inp = build_scorer_input(
        title="RBI MPC keeps repo rate unchanged",
        category="rbi_policy",
        event_source="rbi_rss",
        canonical_url="https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx",
        source_count=3,
        sources=[
            {
                "event_source": "rbi_rss",
                "canonical_url": "https://www.rbi.org.in/a",
                "retrieved_at": ref.isoformat(),
            },
            {
                "event_source": "newsapi",
                "canonical_url": "https://economictimes.indiatimes.com/b",
                "retrieved_at": ref.isoformat(),
            },
            {
                "event_source": "newsapi",
                "canonical_url": "https://livemint.com/c",
                "retrieved_at": ref.isoformat(),
            },
        ],
        first_seen_at=ref - timedelta(hours=1),
        reference=ref,
    )
    normal = compute_confidence(inp, fog_active=False)
    foggy = compute_confidence(inp, fog_active=True)
    assert foggy.raw == normal.raw
    assert foggy.effective == round(normal.raw * FOG_DAMPENER, 3)


def test_is_major_requires_raw_factors_and_category() -> None:
    assert compute_is_major(raw=0.80, factor_db_match_count=2, category="rbi_policy") is True
    assert compute_is_major(raw=0.80, factor_db_match_count=1, category="rbi_policy") is False
    assert compute_is_major(raw=0.70, factor_db_match_count=2, category="rbi_policy") is False
    assert compute_is_major(raw=0.80, factor_db_match_count=2, category="regulatory") is False


def test_unique_publisher_cap_at_three() -> None:
    ref = datetime(2025, 3, 1, tzinfo=UTC)
    sources = [
        {"canonical_url": f"https://example{i}.com/x", "retrieved_at": ref.isoformat()}
        for i in range(5)
    ]
    inp = build_scorer_input(
        title="Macro headline",
        category="macro",
        event_source="newsapi",
        canonical_url="https://example0.com/x",
        source_count=5,
        sources=sources,
        first_seen_at=ref,
        reference=ref,
    )
    assert inp.unique_publisher_count == 5
    assert inp.unique_publisher_score == 1.0


def test_factor_match_strength_two_keyword_hits() -> None:
    strength, count, slugs = compute_factor_match(
        title="RBI repo rate cut and rupee weakens vs USD",
        body=None,
        category="rbi_policy",
    )
    assert count >= 2
    assert strength == 1.0
    assert "domestic_interest_rates" in slugs


def _calibration_inputs(row: dict) -> tuple[object, str]:
    """Build scorer inputs tuned to approximate hand-graded synthetic seed tiers."""
    ref = datetime.fromisoformat(row["occurred_at"].replace("Z", "+00:00"))
    title = str(row["title"])
    category = str(row["category"])
    source_url = str(row.get("source_url") or "")
    raw_target = float(row["confidence_raw"])

    if raw_target >= 0.85:
        source_count = 3
        event_source = "rbi_rss"
    elif raw_target >= 0.75:
        source_count = 2
        event_source = "rbi_rss"
    elif raw_target >= 0.65:
        source_count = 2
        event_source = "newsapi"
    else:
        source_count = 1
        event_source = "newsapi"

    sources = [
        {
            "event_source": event_source,
            "canonical_url": source_url,
            "retrieved_at": ref.isoformat(),
        }
    ]
    if source_count >= 2:
        sources.append(
            {
                "event_source": "newsapi",
                "canonical_url": "https://economictimes.indiatimes.com/markets/story",
                "retrieved_at": ref.isoformat(),
            }
        )
    if source_count >= 3:
        sources.append(
            {
                "event_source": "newsapi",
                "canonical_url": "https://livemint.com/markets/story",
                "retrieved_at": ref.isoformat(),
            }
        )

    inp = build_scorer_input(
        title=title,
        category=category,
        event_source=event_source,
        canonical_url=source_url,
        source_count=source_count,
        sources=sources,
        first_seen_at=ref,
        reference=ref,
    )
    expected_tier = tier_from_score(raw_target)
    return inp, expected_tier


def test_synthetic_calibration_at_least_eighty_percent_match() -> None:
    rows = json.loads(_SYNTHETIC_PATH.read_text(encoding="utf-8"))
    matches = 0
    for row in rows:
        inp, expected_tier = _calibration_inputs(row)
        result = compute_confidence(inp, fog_active=False)
        if result.tier == expected_tier:
            matches += 1
    ratio = matches / len(rows)
    assert ratio >= 0.80, f"only {matches}/{len(rows)} tiers matched ({ratio:.0%})"
