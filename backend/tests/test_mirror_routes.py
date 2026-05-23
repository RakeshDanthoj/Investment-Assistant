"""Mirror API route shapes (P2-S1)."""

from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.mirror import router as mirror_router
from app.core.auth import User, get_current_user
from app.services.mirror_predictions import MirrorPredictionRow
from app.services.mirror_stats import MirrorStatsResult

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
