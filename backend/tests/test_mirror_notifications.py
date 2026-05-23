"""Mirror graded notification routes (P2-S3)."""

from contextlib import contextmanager
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.mirror import router as mirror_router
from app.core.auth import User, get_current_user

app = FastAPI()
app.include_router(mirror_router, prefix="/api")
client = TestClient(app)

TEST_USER = User(id=str(uuid4()), email="mirror-notify@finnwise.test")


@pytest.fixture(autouse=True)
def override_auth():
    async def _user():
        return TEST_USER

    app.dependency_overrides[get_current_user] = _user
    yield
    app.dependency_overrides.clear()


@contextmanager
def _fake_db_connection():
    class _FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    class _FakeConn:
        def cursor(self, **_kwargs):
            return _FakeCursor()

        def commit(self):
            return None

    yield _FakeConn()


@pytest.fixture(autouse=True)
def fake_connection(monkeypatch):
    monkeypatch.setattr(
        "app.api.mirror_notifications.connection",
        _fake_db_connection,
    )


def test_unread_notifications_returns_count_and_items(monkeypatch):
    nid = uuid4()
    cid = uuid4()
    pid = uuid4()
    rows = [
        {
            "id": nid,
            "card_id": cid,
            "prediction_id": pid,
            "payload": {
                "event_title": "Brent supply shock",
                "card_title": "Aviation margin pressure",
                "resolved_at": "2026-05-20T12:00:00+00:00",
            },
            "created_at": datetime(2026, 5, 21, tzinfo=UTC),
        }
    ]

    monkeypatch.setattr(
        "app.api.mirror_notifications.list_unread_card_graded",
        lambda _cur, _uid: rows,
    )

    res = client.get("/api/mirror/notifications/unread")
    assert res.status_code == 200
    payload = res.json()
    assert payload["count"] == 1
    assert payload["items"][0]["event_title"] == "Brent supply shock"
    assert payload["items"][0]["prediction_id"] == str(pid)


def test_unread_empty_list(monkeypatch):
    monkeypatch.setattr(
        "app.api.mirror_notifications.list_unread_card_graded",
        lambda _cur, _uid: [],
    )
    res = client.get("/api/mirror/notifications/unread")
    assert res.status_code == 200
    assert res.json() == {"count": 0, "items": []}


def test_mark_read_returns_ok(monkeypatch):
    monkeypatch.setattr(
        "app.api.mirror_notifications.mark_notification_read",
        lambda *_args, **_kwargs: True,
    )
    res = client.post(f"/api/mirror/notifications/{uuid4()}/read")
    assert res.status_code == 200
    assert res.json() == {"ok": True}


def test_mark_read_not_found(monkeypatch):
    monkeypatch.setattr(
        "app.api.mirror_notifications.mark_notification_read",
        lambda *_args, **_kwargs: False,
    )
    res = client.post(f"/api/mirror/notifications/{uuid4()}/read")
    assert res.status_code == 404
