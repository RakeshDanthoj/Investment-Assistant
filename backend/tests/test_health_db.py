"""Health endpoints including DB connectivity probe."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app


def test_health_ok() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("app.main.connection")
def test_health_db_ok(mock_connection: MagicMock) -> None:
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = (3,)
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_conn.cursor.return_value.__exit__.return_value = None
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_conn
    mock_cm.__exit__.return_value = None

    def side_effect() -> MagicMock:
        from app.diagnostics.timing import record_db_connect, record_db_query

        record_db_connect(12.5)
        record_db_query(3.2)
        return mock_cm

    mock_connection.side_effect = side_effect

    client = TestClient(app)
    response = client.get("/health/db")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["cards"] == 3
    assert body["connect_ms"] == 12.5
    assert body["query_ms"] == 3.2
    assert body["total_ms"] > 0


@patch("app.main.get_settings")
def test_health_db_unconfigured(mock_get_settings: MagicMock) -> None:
    mock_get_settings.return_value.supabase_db_url = ""
    client = TestClient(app)
    response = client.get("/health/db")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "error"
    assert body["code"] == "db_unconfigured"
