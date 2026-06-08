"""Localhost admin dev login (LOCAL_DEV_PASSWORD + ADMIN_EMAILS)."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.local_dev_auth import router as local_dev_auth_router
from app.services.local_dev_auth import (
    LocalDevAuthError,
    is_local_dev_browser_origin,
    local_dev_auth_enabled,
)

app = FastAPI()
app.include_router(local_dev_auth_router, prefix="/api/auth")
client = TestClient(app)

LOCAL_ORIGIN = "http://localhost:3000"


@pytest.fixture(autouse=True)
def _settings(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.settings import get_settings

    monkeypatch.setenv("SUPABASE_URL", "https://test-project.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test-anon-key")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
    monkeypatch.setenv("ADMIN_EMAILS", "owner@example.com")
    monkeypatch.setenv("LOCAL_DEV_PASSWORD", "localdev123")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_local_dev_auth_enabled_when_password_and_service_role_set() -> None:
    assert local_dev_auth_enabled() is True


def test_is_local_dev_browser_origin_accepts_localhost() -> None:
    assert is_local_dev_browser_origin(LOCAL_ORIGIN, None) is True
    assert is_local_dev_browser_origin(None, f"{LOCAL_ORIGIN}/sign-in") is True
    assert is_local_dev_browser_origin("https://prod.example.com", None) is False


def test_local_dev_login_disabled_returns_404(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.settings import get_settings

    monkeypatch.delenv("LOCAL_DEV_PASSWORD", raising=False)
    get_settings.cache_clear()

    res = client.post(
        "/api/auth/local-dev-login",
        json={"email": "owner@example.com", "password": "localdev123"},
        headers={"Origin": LOCAL_ORIGIN},
    )
    assert res.status_code == 404


def test_local_dev_login_rejects_non_local_origin() -> None:
    res = client.post(
        "/api/auth/local-dev-login",
        json={"email": "owner@example.com", "password": "localdev123"},
        headers={"Origin": "https://investment-assistant-frontend.vercel.app"},
    )
    assert res.status_code == 404


def test_local_dev_login_rejects_unknown_email() -> None:
    res = client.post(
        "/api/auth/local-dev-login",
        json={"email": "other@example.com", "password": "localdev123"},
        headers={"Origin": LOCAL_ORIGIN},
    )
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid email or password"


def test_local_dev_login_rejects_wrong_password() -> None:
    res = client.post(
        "/api/auth/local-dev-login",
        json={"email": "owner@example.com", "password": "wrong-password"},
        headers={"Origin": LOCAL_ORIGIN},
    )
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_local_dev_login_service_success() -> None:
    with patch(
        "app.api.local_dev_auth.local_dev_login",
        new=AsyncMock(
            return_value={
                "access_token": "access-token",
                "refresh_token": "refresh-token",
                "expires_in": 3600,
                "token_type": "bearer",
            }
        ),
    ):
        res = client.post(
            "/api/auth/local-dev-login",
            json={"email": "owner@example.com", "password": "localdev123"},
            headers={"Origin": LOCAL_ORIGIN},
        )

    assert res.status_code == 200
    body = res.json()
    assert body["access_token"] == "access-token"
    assert body["refresh_token"] == "refresh-token"


@pytest.mark.asyncio
async def test_local_dev_login_service_maps_auth_errors() -> None:
    with patch(
        "app.api.local_dev_auth.local_dev_login",
        new=AsyncMock(side_effect=LocalDevAuthError("Invalid email or password", 401)),
    ):
        res = client.post(
            "/api/auth/local-dev-login",
            json={"email": "owner@example.com", "password": "localdev123"},
            headers={"Origin": LOCAL_ORIGIN},
        )

    assert res.status_code == 401
