"""Editor watchlist API access control and escalate shape."""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.editor_watchlist import router as editor_watchlist_router
from app.core.auth import User, get_current_user

app = FastAPI()
app.include_router(editor_watchlist_router, prefix="/api")
client = TestClient(app)

ADMIN = User(id=str(uuid4()), email="owner@example.com")
OTHER = User(id=str(uuid4()), email="other@example.com")
ITEM_ID = "a1000001-0001-4001-8001-000000000001"


@pytest.fixture(autouse=True)
def _admin_env(monkeypatch):
    from app.core.settings import get_settings

    monkeypatch.setenv("ADMIN_EMAILS", "owner@example.com")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_watchlist_list_requires_admin():
    async def _other():
        return OTHER

    app.dependency_overrides[get_current_user] = _other
    res = client.get("/api/editor/watchlist")
    app.dependency_overrides.clear()
    assert res.status_code == 403


def test_escalate_returns_event_id(monkeypatch):
    async def _admin():
        return ADMIN

    app.dependency_overrides[get_current_user] = _admin
    event_id = uuid4()
    monkeypatch.setattr(
        "app.api.editor_watchlist.watchlist_svc.escalate_watchlist_item",
        lambda _id: (
            {
                "id": ITEM_ID,
                "event_description": "Test",
                "category": "macro",
                "added_at": "2026-05-30T12:00:00+00:00",
                "review_frequency": "weekly",
                "status": "escalated",
                "escalated_event_id": str(event_id),
            },
            event_id,
        ),
    )

    res = client.post(f"/api/editor/watchlist/{ITEM_ID}/escalate")
    app.dependency_overrides.clear()

    assert res.status_code == 200
    body = res.json()
    assert body["event_id"] == str(event_id)
    assert body["item"]["status"] == "escalated"
