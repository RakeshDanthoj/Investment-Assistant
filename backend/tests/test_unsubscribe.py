"""Unsubscribe token single-shot behavior (P2-S10)."""

from __future__ import annotations

from contextlib import contextmanager
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.unsubscribe import apply_unsubscribe_token, router

app = FastAPI()
app.include_router(router)
client = TestClient(app)


@contextmanager
def _fake_connection_factory(rows_by_query: dict[str, list]):
    class _FakeCursor:
        def __init__(self):
            self._rows = rows_by_query
            self._last_sql = ""

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, sql, params=None):
            self._last_sql = " ".join(sql.split())
            key = "token_lookup" if "unsubscribe_tokens" in sql and "FOR UPDATE" in sql else ""
            if "UPDATE public.unsubscribe_tokens" in sql:
                key = "mark_used"
            if "user_email_preferences" in sql:
                key = "prefs"

        def fetchone(self):
            if "SELECT user_id" in self._last_sql:
                return rows_by_query.get("token_lookup", [None])[0]
            return None

    class _FakeConn:
        def cursor(self, **_kwargs):
            return _FakeCursor()

        def transaction(self):
            @contextmanager
            def _tx():
                yield

            return _tx()

    @contextmanager
    def _conn():
        yield _FakeConn()

    return _conn


def test_apply_unsubscribe_rejects_invalid_token():
    assert apply_unsubscribe_token("not-a-uuid") is False


def test_unsubscribe_endpoint_success(monkeypatch):
    token = str(uuid4())
    user_id = str(uuid4())

    class _Row:
        def __init__(self):
            self.used = None

    state = {"row": {"user_id": user_id, "used_at": None}}

    @contextmanager
    def fake_connection():
        class _Cur:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def execute(self, sql, params=None):
                self.sql = sql

            def fetchone(self):
                if "FOR UPDATE" in self.sql:
                    return state["row"]
                return None

        class _Conn:
            def cursor(self, **_kwargs):
                return _Cur()

            def transaction(self):
                @contextmanager
                def _tx():
                    yield

                return _tx()

        yield _Conn()

    monkeypatch.setattr("app.api.unsubscribe.connection", fake_connection)
    res = client.get(f"/unsubscribe?token={token}")
    assert res.status_code == 200
    assert "unsubscribed" in res.text.lower()


def test_unsubscribe_endpoint_invalid_token(monkeypatch):
    @contextmanager
    def fake_connection():
        class _Cur:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def execute(self, sql, params=None):
                self.sql = sql

            def fetchone(self):
                return None

        class _Conn:
            def cursor(self, **_kwargs):
                return _Cur()

            def transaction(self):
                @contextmanager
                def _tx():
                    yield

                return _tx()

        yield _Conn()

    monkeypatch.setattr("app.api.unsubscribe.connection", fake_connection)
    res = client.get(f"/unsubscribe?token={uuid4()}")
    assert res.status_code == 404
