"""Feed filtering: profile + category merge (P1-S9)."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

from app.services.feed import (
    SessionProfileRow,
    build_card_payload,
    build_feed_response,
    confidence_tier,
)


def test_confidence_tier_buckets() -> None:
    assert confidence_tier(85) == "high"
    assert confidence_tier(55) == "moderate"
    assert confidence_tier(20) == "uncertain"


def test_build_card_payload_direction_and_magnitude_differ() -> None:
    row = {
        "id": "x",
        "headline": "H",
        "insight_layer": ("Domestic banks face margin pressure as funding costs " * 8).strip(),
        "lifecycle_state": "published",
        "created_at": None,
        "updated_at": None,
        "event_title": "Event",
        "category": "macro",
        "confidence_score": 80,
        "instruments": [{"instrument_id": "ABC", "signal_type": "watch"}],
    }
    out = build_card_payload(row)
    assert out["direction_confidence"]["tier"] == "high"
    assert out["magnitude_confidence"]["tier"] == "moderate"
    assert len(out["insight_excerpt"]) <= 323


@patch("app.services.feed.fetch_fog_of_war_flag", return_value=True)
@patch("app.services.feed.fetch_pulse_rows")
@patch("app.services.feed.fetch_session_profile")
def test_build_feed_splits_category_param(
    mock_profile: MagicMock,
    mock_rows: MagicMock,
    mock_fog: MagicMock,
) -> None:
    mock_profile.return_value = None
    mock_rows.return_value = ([], None)
    out = build_feed_response(session_id=None, horizon=None, category="macro, rbi_policy ")
    mock_rows.assert_called_once()
    assert mock_rows.call_args.kwargs["categories"] == ["macro", "rbi_policy"]
    assert out["fog_of_war"] is True
    mock_fog.assert_called_once()


@patch("app.services.feed.fetch_fog_of_war_flag", return_value=False)
@patch("app.services.feed.fetch_pulse_rows")
@patch("app.services.feed.fetch_session_profile")
def test_build_feed_loads_session_profile(
    mock_profile: MagicMock,
    mock_rows: MagicMock,
    mock_fog: MagicMock,
) -> None:
    sid = uuid4()
    prof = SessionProfileRow(horizon="1_3y", mode="portfolio_protector")
    mock_profile.return_value = prof
    mock_rows.return_value = ([], prof)
    out = build_feed_response(session_id=sid, horizon=None, category=None)
    mock_profile.assert_called_once_with(sid)
    mock_rows.assert_called_once()
    assert mock_rows.call_args.kwargs["profile"] == prof
    assert mock_rows.call_args.kwargs["horizon_override"] is None
    assert out["profile"]["horizon"] == "1_3y"
    mock_fog.assert_called_once()
