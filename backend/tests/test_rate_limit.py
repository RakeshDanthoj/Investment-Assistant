"""Lens per-user daily rate limit (P2-S13)."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.lens import router as lens_router
from app.core.auth import User, get_current_user
from app.middleware.rate_limit import LensDailyRateLimitError, enforce_lens_daily_limit
from app.services.lens_queries import LensQueryRow

app = FastAPI()
app.include_router(lens_router, prefix="/api")
client = TestClient(app)

TEST_USER = User(id=str(uuid4()), email="rate@finnwise.test")


@pytest.fixture(autouse=True)
def override_auth():
    async def _user():
        return TEST_USER

    app.dependency_overrides[get_current_user] = _user
    yield
    app.dependency_overrides.clear()


def test_enforce_lens_daily_limit_raises_with_retry_after(monkeypatch):
    monkeypatch.setattr(
        "app.middleware.rate_limit.try_consume_lens_query_slot",
        lambda **_: False,
    )
    monkeypatch.setattr(
        "app.middleware.rate_limit._seconds_until_utc_midnight",
        lambda: 42,
    )

    with pytest.raises(LensDailyRateLimitError) as exc_info:
        enforce_lens_daily_limit(user_id=uuid4())

    assert exc_info.value.retry_after_seconds == 42


def test_post_lens_query_returns_429_with_retry_after(monkeypatch):
    def _raise_limit(**_kwargs):
        raise LensDailyRateLimitError(retry_after_seconds=99)

    monkeypatch.setattr("app.api.lens.enforce_lens_daily_limit", _raise_limit)

    res = client.post(
        "/api/lens/queries",
        json={"query": "What would a US recession mean for Indian IT exporters?"},
    )
    assert res.status_code == 429
    assert res.headers.get("retry-after") == "99"
    assert res.json()["detail"]["code"] == "lens_daily_rate_limit"


def test_post_lens_query_succeeds_when_under_limit(monkeypatch):
    query_id = uuid4()
    row = LensQueryRow(
        id=query_id,
        query="How might RBI hold rates through monsoon?",
        sector=None,
        horizon=None,
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
        json={"query": "How might RBI hold rates through monsoon season?"},
    )
    assert res.status_code == 201
