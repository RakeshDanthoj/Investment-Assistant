from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.core.auth import User, get_current_user
from app.main import app
from app.services import factor_db as factor_db_svc


@pytest.fixture(autouse=True)
def _clear_app_overrides_and_settings_cache() -> None:
    yield
    app.dependency_overrides.clear()
    from app.core.settings import get_settings

    get_settings.cache_clear()


@pytest.fixture()
def authenticated_user(monkeypatch: pytest.MonkeyPatch) -> str:
    from app.core.settings import get_settings

    monkeypatch.setenv("FACTOR_DB_ADMIN_EMAILS", "owner@example.com")
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)
    get_settings.cache_clear()

    async def _user():
        return User(id="111", email="owner@example.com")

    app.dependency_overrides[get_current_user] = _user

    yield "owner@example.com"

    app.dependency_overrides.pop(get_current_user, None)


def test_sensitivity_endpoint_returns_mocked_row(
    monkeypatch: pytest.MonkeyPatch,
    authenticated_user: str,
) -> None:
    assert authenticated_user == "owner@example.com"
    from app.core.settings import get_settings

    get_settings.cache_clear()
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)

    sample = factor_db_svc.SensitivityLookup(
        ticker="SBIN",
        factor_slug="crude_oil",
        sensitivity=-3,
        mmj_tag="JUDGED",
        source_url="https://example.doc",
        retrieved_at=datetime(2026, 3, 15, tzinfo=UTC),
        freshness="green",
        instrument_display_name="State Bank of India",
    )
    monkeypatch.setattr(factor_db_svc, "lookup_sensitivity", MagicMock(return_value=sample))

    client = TestClient(app)
    r = client.get(
        "/api/factor-db/sensitivity",
        params={"instrument": "SBIN", "factor": "crude_oil"},
        headers={"Authorization": "Bearer dummy"},
    )

    assert r.status_code == 200, r.text
    body = r.json()
    assert body["instrument_ticker"] == "SBIN"
    assert body["freshness"] == "green"


def test_matrix_requires_admin(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.settings import get_settings

    monkeypatch.setenv("FACTOR_DB_ADMIN_EMAILS", "owner@example.com")
    monkeypatch.delenv("SUPABASE_DB_URL", raising=False)
    get_settings.cache_clear()

    async def _other():
        return User(id="222", email="other@example.com")

    app.dependency_overrides[get_current_user] = _other

    client = TestClient(app)
    r = client.get(
        "/api/factor-db/matrix",
        headers={"Authorization": "Bearer dummy"},
    )

    assert r.status_code == 403

    app.dependency_overrides.pop(get_current_user, None)
