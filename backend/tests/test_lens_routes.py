"""Lens API route shapes (P2-S6) and read-view consolidation (PI-S3)."""

from contextlib import contextmanager
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.lens import router as lens_router
from app.core.auth import User, get_current_user
from app.diagnostics.timing import DbRequestTimer, record_db_connect, record_db_query
from app.services.lens_queries import LensQueryRow, list_recent_for_user

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

    monkeypatch.setattr("app.api.lens.enforce_lens_daily_limit", lambda **_: None)
    monkeypatch.setattr("app.api.lens.check_monthly_budget_or_raise", lambda **_: None)
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


def test_list_recent_for_user_uses_single_connection() -> None:
    user_id = uuid4()
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchall.return_value = []
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_conn.cursor.return_value.__exit__.return_value = None

    @contextmanager
    def conn_with_cursor():
        record_db_connect(0.1)
        try:
            yield mock_conn
        finally:
            record_db_query(0.5)

    with patch("app.services.lens_queries.connection", conn_with_cursor):
        with DbRequestTimer() as timer:
            rows = list_recent_for_user(user_id)

    assert rows == []
    assert timer.snapshot()["connection_count"] == 1
    sql = mock_cur.execute.call_args[0][0]
    assert "lens_user_queries_v" in sql
    assert mock_cur.execute.call_args[0][1] == (str(user_id), 20)
