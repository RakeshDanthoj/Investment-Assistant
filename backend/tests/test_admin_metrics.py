"""Admin metrics endpoint shape and access control (P2-S13)."""

from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.admin_metrics import router as admin_metrics_router
from app.core.auth import User, get_current_user

app = FastAPI()
app.include_router(admin_metrics_router, prefix="/api/admin")
client = TestClient(app)

ADMIN = User(id=str(uuid4()), email="owner@example.com")
OTHER = User(id=str(uuid4()), email="other@example.com")

SAMPLE_METRICS = {
    "as_of": "2026-05-24T12:00:00+00:00",
    "window_days": 30,
    "daily_card_count": 3,
    "p95_generation_time_ms": 45000.0,
    "high_confidence_override_rate": 0.1,
    "signal_false_positive_rate": 0.1,
    "high_confidence_gate_total": 10,
    "high_confidence_gate_overridden": 1,
}


@pytest.fixture(autouse=True)
def _clear_settings_cache(monkeypatch):
    from app.core.settings import get_settings

    monkeypatch.setenv("ADMIN_EMAILS", "owner@example.com")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_admin_metrics_requires_admin_email():
    async def _other():
        return OTHER

    app.dependency_overrides[get_current_user] = _other
    res = client.get("/api/admin/metrics")
    app.dependency_overrides.clear()
    assert res.status_code == 403


def test_admin_metrics_returns_expected_shape(monkeypatch):
    async def _admin():
        return ADMIN

    app.dependency_overrides[get_current_user] = _admin
    monkeypatch.setattr(
        "app.api.admin_metrics.fetch_admin_metrics",
        lambda **_: dict(SAMPLE_METRICS),
    )

    res = client.get("/api/admin/metrics")
    app.dependency_overrides.clear()

    assert res.status_code == 200
    payload = res.json()
    assert payload["daily_card_count"] == 3
    assert payload["p95_generation_time_ms"] == 45000.0
    assert payload["signal_false_positive_rate"] == 0.1
    assert payload["high_confidence_override_rate"] == 0.1
    assert payload["high_confidence_gate_total"] == 10
