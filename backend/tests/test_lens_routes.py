"""Lens API route shapes (P2-S6)."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.lens import router as lens_router
from app.core.auth import User, get_current_user
from app.services.lens_queries import LensQueryRow

app = FastAPI()
app.include_router(lens_router, prefix="/api")
client = TestClient(app)

TEST_USER = User(id=str(uuid4()), email="lens@finnwise.test")


@pytest.fixture(autouse=True)
def override_auth():
    async def _user():
        return TEST_USER

    app.dependency_overrides[get_current_user] = _user
    yield
    app.dependency_overrides.clear()


def test_lens_queries_me_requires_auth_when_not_overridden():
    app.dependency_overrides.clear()
    res = client.get("/api/lens/queries/me")
    assert res.status_code == 401


def test_post_lens_query_returns_id(monkeypatch):
    query_id = uuid4()
    row = LensQueryRow(
        id=query_id,
        query="What would a US recession mean for Indian IT exporters?",
        sector="macro",
        horizon="3_7y",
        status="queued",
        card_id=None,
        created_at=datetime(2026, 5, 24, tzinfo=UTC),
    )

    monkeypatch.setattr("app.api.lens.create_query", lambda **_kwargs: row)
    monkeypatch.setattr("app.api.lens.enqueue_generation", lambda _qid: None)

    res = client.post(
        "/api/lens/queries",
        json={
            "query": "What would a US recession mean for Indian IT exporters?",
            "sector": "macro",
            "horizon": "3_7y",
        },
    )
    assert res.status_code == 201
    payload = res.json()
    assert payload["id"] == str(query_id)
    assert payload["status"] == "queued"


def test_post_lens_query_rejects_short_input():
    res = client.post("/api/lens/queries", json={"query": "too short"})
    assert res.status_code == 422


def test_lens_queries_me_returns_items(monkeypatch):
    row = LensQueryRow(
        id=uuid4(),
        query="How might RBI hold rates through monsoon?",
        sector="rbi_policy",
        horizon=None,
        status="done",
        card_id=uuid4(),
        created_at=datetime(2026, 5, 20, tzinfo=UTC),
    )
    monkeypatch.setattr(
        "app.api.lens.list_recent_for_user",
        lambda _uid, **_: [row],
    )

    res = client.get("/api/lens/queries/me")
    assert res.status_code == 200
    payload = res.json()
    assert payload["items"][0]["query"] == row.query
    assert payload["items"][0]["status"] == "done"
