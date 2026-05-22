"""Prediction route maps domain errors to HTTP (P1-S12)."""

from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.predictions import router as predictions_router
from app.core.auth import User, get_current_user
from app.services.predictions import DuplicatePredictionError

app = FastAPI()
app.include_router(predictions_router, prefix="/api")
client = TestClient(app)

TEST_USER = User(id=str(uuid4()), email="tester@finnwise.test")


@pytest.fixture(autouse=True)
def override_auth():
    async def _user():
        return TEST_USER

    app.dependency_overrides[get_current_user] = _user
    yield
    app.dependency_overrides.clear()


def test_post_prediction_requires_auth_when_not_overridden():
    app.dependency_overrides.clear()
    res = client.post(
        "/api/predictions",
        json={
            "card_id": str(uuid4()),
            "prediction_text": "Option A narrative long enough",
        },
    )
    assert res.status_code == 401


def test_post_prediction_duplicate_maps_to_409_with_prior_value(monkeypatch):
    prior = "Primary thesis unfolds - mechanisms align with the stated horizon."

    def _raise(**_kwargs):
        raise DuplicatePredictionError(prior)

    monkeypatch.setattr("app.api.predictions.log", _raise)

    res = client.post(
        "/api/predictions",
        json={
            "card_id": str(uuid4()),
            "prediction_text": "Option A narrative long enough",
        },
    )
    assert res.status_code == 409
    detail = res.json()["detail"]
    assert detail["code"] == "duplicate_prediction"
    assert detail["prediction_text"] == prior


def test_post_prediction_propagates_success(monkeypatch):
    seen: dict = {}

    def _capture(**kwargs):
        seen.update(kwargs)

    monkeypatch.setattr("app.api.predictions.log", _capture)

    cid = uuid4()
    body = {
        "card_id": str(cid),
        "prediction_text": "Structured view - thesis confirms within horizon",
    }
    res = client.post("/api/predictions", json=body)
    assert res.status_code == 200
    assert seen["card_id"] == cid
    assert str(seen["user_id"]) == TEST_USER.id


def test_get_predictions_me_returns_user_rows(monkeypatch):
    from datetime import UTC, datetime

    from app.services.predictions import UserPredictionRow

    cid = uuid4()
    logged_at = datetime(2026, 5, 21, 12, 0, tzinfo=UTC)
    row = UserPredictionRow(
        card_id=cid,
        prediction_text="Mixed - competing mechanisms cancel; outcome stays ambiguous.",
        logged_at=logged_at,
    )

    monkeypatch.setattr("app.api.predictions.list_for_user", lambda _uid, limit=100: [row])

    res = client.get("/api/predictions/me")
    assert res.status_code == 200
    payload = res.json()
    assert payload["items"][0]["card_id"] == str(cid)
    assert payload["items"][0]["prediction_text"] == row.prediction_text
