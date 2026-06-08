"""P2-S11 — Map API sector list, detail, and gap-type module links."""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.auth import User, get_current_user
from app.db.migrate import apply_migrations
from app.db.seeds import apply_all_factor_db_seeds
from app.diagnostics.timing import DbRequestTimer, record_db_connect, record_db_query
from app.http.cache_control import MAP_READ_CACHE
from app.main import app
from app.services.reasoning_gap_map import ALL_GAP_TYPES

TEST_USER = User(id=str(uuid4()), email="map@finnwise.test")


@pytest.fixture(scope="module")
def map_client(db_connection):
    apply_migrations(db_connection)
    apply_all_factor_db_seeds(db_connection)
    db_connection.commit()
    return TestClient(app)


@pytest.fixture(autouse=True)
def override_auth():
    async def _user():
        return TEST_USER

    app.dependency_overrides[get_current_user] = _user
    yield
    app.dependency_overrides.clear()


def test_list_sectors_returns_eight(map_client) -> None:
    res = map_client.get("/api/map/sectors", headers={"Authorization": "Bearer t"})
    assert res.status_code == 200
    slugs = {s["slug"] for s in res.json()["sectors"]}
    assert "banking" in slugs
    assert "it" in slugs
    assert len(slugs) >= 8


def test_sector_summary_has_modules_without_matrix(map_client) -> None:
    res = map_client.get("/api/map/sectors/banking", headers={"Authorization": "Bearer t"})
    assert res.status_code == 200
    body = res.json()
    assert body["sector"]["slug"] == "banking"
    assert len(body["modules"]) >= 1
    assert body["modules"][0]["title"].startswith("How ")
    assert body["instrument_count"] >= 1
    assert "factors" not in body
    assert "sensitivities" not in body
    assert res.headers["Cache-Control"] == MAP_READ_CACHE


def test_sector_matrix_has_factors_and_sensitivities(map_client) -> None:
    res = map_client.get(
        "/api/map/sectors/banking/matrix",
        headers={"Authorization": "Bearer t"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["sector"]["slug"] == "banking"
    assert len(body["factors"]) == 8
    assert len(body["instruments"]) >= 1
    assert body["instrument_count"] >= len(body["instruments"])
    assert res.headers["Cache-Control"] == MAP_READ_CACHE


def test_gap_type_modules_resolve(map_client) -> None:
    for gap in ALL_GAP_TYPES:
        res = map_client.get(
            f"/api/map/modules/by-gap-type?gap_type={gap}",
            headers={"Authorization": "Bearer t"},
        )
        assert res.status_code == 200
        items = res.json()["items"]
        assert len(items) == 1
        assert items[0]["gap_type"] == gap
        assert items[0]["module"]["id"]
        assert items[0]["module"]["title"]



@patch("app.services.map_content.connection")
def test_fetch_sector_summary_single_connection(mock_connection: MagicMock) -> None:
    from app.services import map_content as map_svc

    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = {
        "slug": "banking",
        "name": "Banking",
        "instrument_count": 5,
        "modules": [],
    }
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_conn.cursor.return_value.__exit__.return_value = None

    @contextmanager
    def conn_with_cursor():
        record_db_connect(0.1)
        try:
            yield mock_conn
        finally:
            record_db_query(0.5)

    mock_connection.side_effect = conn_with_cursor

    with DbRequestTimer() as timer:
        payload = map_svc.fetch_sector_summary(sector_slug="banking")

    assert payload["sector"]["slug"] == "banking"
    assert timer.snapshot()["connection_count"] == 1
    assert mock_cur.execute.call_count == 1


@patch("app.services.map_content.connection")
def test_fetch_sector_matrix_single_connection(mock_connection: MagicMock) -> None:
    from app.services import map_content as map_svc

    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = {
        "sector": {"slug": "banking", "name": "Banking"},
        "factors": [{"slug": "rates", "display_name": "Rates", "sort_order": 1, "description": ""}],
        "instruments": [
            {
                "id": "00000000-0000-4000-8000-000000000001",
                "ticker": "HDFCBANK",
                "display_name": "HDFC Bank",
            }
        ],
        "sensitivity_rows": [],
    }
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_conn.cursor.return_value.__exit__.return_value = None

    @contextmanager
    def conn_with_cursor():
        record_db_connect(0.1)
        try:
            yield mock_conn
        finally:
            record_db_query(0.5)

    mock_connection.side_effect = conn_with_cursor

    with DbRequestTimer() as timer:
        payload = map_svc.fetch_sector_matrix(sector_slug="banking")

    assert payload["sector"]["slug"] == "banking"
    assert timer.snapshot()["connection_count"] == 1
    assert mock_cur.execute.call_count == 1
