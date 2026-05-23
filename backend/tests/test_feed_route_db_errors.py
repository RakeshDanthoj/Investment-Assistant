"""Feed route returns CORS-safe 503 when SUPABASE_DB_URL is misconfigured."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.core.settings import get_settings
from app.main import app

_ORIGIN = "https://investment-assistant-frontend.vercel.app"


def _client_with_db_url(db_url: str, monkeypatch) -> TestClient:
    monkeypatch.setenv("SUPABASE_DB_URL", db_url)
    get_settings.cache_clear()
    return TestClient(app)


def test_feed_missing_db_url_returns_503_with_cors(monkeypatch) -> None:
    client = _client_with_db_url("", monkeypatch)
    response = client.get("/api/feed", headers={"Origin": _ORIGIN})
    assert response.status_code == 503
    assert response.headers.get("access-control-allow-origin") == _ORIGIN
    assert response.json()["detail"]["code"] == "db_unavailable"


def test_feed_bare_project_ref_returns_503_with_cors(monkeypatch) -> None:
    client = _client_with_db_url("coqihzykxemmyewakasj", monkeypatch)
    response = client.get("/api/feed", headers={"Origin": _ORIGIN})
    assert response.status_code == 503
    assert response.headers.get("access-control-allow-origin") == _ORIGIN
    detail = response.json()["detail"]
    assert detail["code"] == "db_unavailable"
    assert "full PostgreSQL URI" in detail["message"]
