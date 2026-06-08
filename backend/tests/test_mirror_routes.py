"""Mirror API route shapes (P2-S1 / PI-S2)."""

from contextlib import contextmanager
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.mirror import router as mirror_router
from app.core.auth import User, get_current_user
from app.diagnostics.timing import DbRequestTimer, record_db_connect, record_db_query
from app.services.mirror_dashboard import MirrorDashboardBundle, build_mirror_dashboard
from app.services.mirror_predictions import MirrorPredictionRow
from app.services.mirror_stats import MirrorStatsResult
from app.services.mirror_streak import MirrorStreakResult, StreakCell

app = FastAPI()
app.include_router(mirror_router, prefix="/api")
client = TestClient(app)

TEST_USER = User(id=str(uuid4()), email="mirror@finnwise.test")


@pytest.fixture(autouse=True)
def override_auth():
    async def _user():
        return TEST_USER

    app.dependency_overrides[get_current_user] = _user
    yield
    app.dependency_overrides.clear()


def test_mirror_predictions_requires_auth_when_not_overridden():
    app.dependency_overrides.clear()
    res = client.get("/api/mirror/predictions")
    assert res.status_code == 401


def test_mirror_predictions_returns_items(monkeypatch):
    from datetime import UTC, datetime

    row = MirrorPredictionRow(
        id=uuid4(),
        card_id=uuid4(),
        prediction_text="Mixed - competing mechanisms cancel; outcome stays ambiguous.",
        logged_at=datetime(2026, 5, 21, tzinfo=UTC),
        mechanism_accuracy=None,
        business_accuracy=None,
        market_accuracy=None,
        gap_insight=None,
        card_title="Aviation faces margin pressure",
        event_title="Brent supply shock",
        event_category="macro",
        lifecycle_state="active",
        mirror_status="active",
        linked_map_module_id=None,
        linked_map_module_name=None,
    )

    monkeypatch.setattr(
        "app.api.mirror.list_predictions",
        lambda *_args, **_kwargs: [row],
    )

    res = client.get("/api/mirror/predictions?status=active")
    assert res.status_code == 200
    payload = res.json()
    assert payload["items"][0]["card_title"] == row.card_title
    assert payload["items"][0]["mirror_status"] == "active"


def test_mirror_stats_returns_strip(monkeypatch):
    stats = MirrorStatsResult(
        total_predictions=4,
        mechanism_accuracy_pct=75.0,
        market_accuracy_pct=50.0,
        reasoning_gaps_found=2,
        mechanism_tone="strong",
        market_tone="developing",
    )
    monkeypatch.setattr("app.api.mirror.stats_for_user", lambda _uid: stats)

    res = client.get("/api/mirror/stats")
    assert res.status_code == 200
    payload = res.json()
    assert payload["total_predictions"] == 4
    assert payload["mechanism_tone"] == "strong"
    assert payload["market_tone"] == "developing"


def _sample_dashboard_bundle() -> MirrorDashboardBundle:
    stats = MirrorStatsResult(
        total_predictions=1,
        mechanism_accuracy_pct=100.0,
        market_accuracy_pct=None,
        reasoning_gaps_found=0,
        mechanism_tone="neutral",
        market_tone="neutral",
    )
    row = MirrorPredictionRow(
        id=uuid4(),
        card_id=uuid4(),
        prediction_text="Test",
        logged_at=datetime(2026, 5, 21, tzinfo=UTC),
        mechanism_accuracy=None,
        business_accuracy=None,
        market_accuracy=None,
        gap_insight=None,
        card_title="Card",
        event_title="Event",
        event_category="macro",
        lifecycle_state="active",
        mirror_status="active",
        linked_map_module_id=None,
        linked_map_module_name=None,
    )
    streak = MirrorStreakResult(
        cells=[StreakCell(letter="·", grade="empty")],
        mechanism_accuracy_pct=None,
        market_accuracy_pct=None,
        summary="No graded predictions yet.",
    )
    return MirrorDashboardBundle(
        stats=stats,
        predictions=[row],
        limit=50,
        offset=0,
        streak=streak,
        gaps=[],
        insufficient_gaps_history=True,
        unread_notification_rows=[],
    )


def test_mirror_dashboard_returns_combined_payload(monkeypatch):
    bundle = _sample_dashboard_bundle()
    monkeypatch.setattr(
        "app.api.mirror.build_mirror_dashboard",
        lambda *_a, **_k: bundle,
    )

    res = client.get("/api/mirror/dashboard")
    assert res.status_code == 200
    payload = res.json()
    assert payload["stats"]["total_predictions"] == 1
    assert len(payload["predictions"]["items"]) == 1
    assert payload["streak"]["summary"] == bundle.streak.summary
    assert payload["gaps"]["insufficient_history"] is True
    assert payload["unread_notifications"]["count"] == 0


@patch("app.services.mirror_dashboard.list_unread_card_graded", return_value=[])
@patch("app.services.mirror_dashboard.connection")
def test_build_mirror_dashboard_uses_single_connection(
    mock_connection: MagicMock,
    mock_unread: MagicMock,
) -> None:
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchall.side_effect = [[], []]
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_conn.cursor.return_value.__exit__.return_value = None

    @contextmanager
    def conn_with_cursor():
        record_db_connect(0.1)
        try:
            yield mock_conn
        finally:
            record_db_query(0.5)

    mock_connection.side_effect = conn_with_cursor

    with DbRequestTimer() as timer:
        build_mirror_dashboard(uuid4())

    assert timer.snapshot()["connection_count"] == 1
    assert mock_cur.execute.call_count == 2
    mock_unread.assert_called_once()
