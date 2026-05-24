"""Saved threads API — idempotent save per (user, card) (P2-S8)."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.saved_threads import router as saved_threads_router
from app.core.auth import User, get_current_user
from app.services.saved_threads import SavedThreadRow

app = FastAPI()
app.include_router(saved_threads_router, prefix="/api")
client = TestClient(app)

TEST_USER = User(id=str(uuid4()), email="saved@finnwise.test")
CARD_ID = uuid4()


@pytest.fixture(autouse=True)
def override_auth():
    async def _user():
        return TEST_USER

    app.dependency_overrides[get_current_user] = _user
    yield
    app.dependency_overrides.clear()


def test_post_saved_thread_requires_auth_when_not_overridden():
    app.dependency_overrides.clear()
    res = client.post("/api/saved-threads", json={"card_id": str(CARD_ID)})
    assert res.status_code == 401


def test_post_saved_thread_creates_then_idempotent(monkeypatch):
    saved_at = datetime(2026, 5, 24, 12, 0, tzinfo=UTC)
    calls: list[bool] = []

    def fake_save(*, user_id, card_id):  # noqa: ANN001
        _ = user_id, card_id
        if not calls:
            calls.append(True)
            return True, saved_at
        return False, saved_at

    monkeypatch.setattr("app.api.saved_threads.card_exists", lambda _cid: True)
    monkeypatch.setattr("app.api.saved_threads.save_card", fake_save)

    first = client.post("/api/saved-threads", json={"card_id": str(CARD_ID)})
    assert first.status_code == 201
    assert first.json()["created"] is True

    second = client.post("/api/saved-threads", json={"card_id": str(CARD_ID)})
    assert second.status_code == 200
    assert second.json()["created"] is False


def test_post_saved_thread_404_when_card_missing(monkeypatch):
    monkeypatch.setattr("app.api.saved_threads.card_exists", lambda _cid: False)
    res = client.post("/api/saved-threads", json={"card_id": str(CARD_ID)})
    assert res.status_code == 404


def test_get_saved_threads_lists_items(monkeypatch):
    row = SavedThreadRow(
        card_id=CARD_ID,
        card_title="US recession impact on IT exporters",
        event_category="macro",
        saved_at=datetime(2026, 5, 24, 12, 0, tzinfo=UTC),
    )
    monkeypatch.setattr(
        "app.api.saved_threads.list_for_user",
        lambda _uid: [row],
    )
    res = client.get("/api/saved-threads")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["card_title"] == row.card_title
