"""Prediction route maps domain errors to HTTP (P1-S10)."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.prediction_log import PredictionLogError

client = TestClient(app)


def test_post_prediction_duplicate_maps_to_409(monkeypatch):
    def _raise(**_kwargs):
        raise PredictionLogError("duplicate_prediction")

    monkeypatch.setattr("app.api.predictions.log_prediction", _raise)

    res = client.post(
        "/api/predictions",
        json={
            "card_id": str(uuid4()),
            "user_id": str(uuid4()),
            "prediction_text": "Option A narrative long enough",
        },
    )
    assert res.status_code == 409


def test_post_prediction_propagates_success(monkeypatch):
    seen: dict = {}

    def _capture(**kwargs):
        seen.update(kwargs)

    monkeypatch.setattr("app.api.predictions.log_prediction", _capture)

    cid = uuid4()
    uid = uuid4()
    body = {
        "card_id": str(cid),
        "user_id": str(uid),
        "prediction_text": "Structured view — thesis confirms within horizon",
    }
    res = client.post("/api/predictions", json=body)
    assert res.status_code == 200
    assert seen["card_id"] == cid
    assert seen["user_id"] == uid
