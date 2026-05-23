"""Health endpoints including DB connectivity probe."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.db.connection import close_db_pool, init_db_pool
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


def test_db_pool_lifecycle_init_and_close() -> None:
    import app.db.connection as conn_module

    close_db_pool()
    with patch("app.db.connection.get_settings") as mock_get_settings:
        mock_get_settings.return_value.supabase_db_url = ""
        init_db_pool()
        assert conn_module._pool is None

    with patch("app.db.connection.ConnectionPool") as mock_pool_cls:
        mock_pool = MagicMock()
        mock_pool_cls.return_value = mock_pool
        with patch("app.db.connection.get_settings") as mock_get_settings:
            mock_get_settings.return_value.supabase_db_url = (
                "postgresql://postgres:secret@db.example.supabase.co:5432/postgres"
            )
            init_db_pool()
            mock_pool_cls.assert_called_once()
            kwargs = mock_pool_cls.call_args.kwargs
            assert kwargs["min_size"] == 1
            assert kwargs["max_size"] == 10
            assert kwargs["kwargs"]["connect_timeout"] == 10
            close_db_pool()
            mock_pool.close.assert_called_once()
            assert conn_module._pool is None

    close_db_pool()


def test_health_db_with_lifespan_skips_pool_when_unconfigured() -> None:
    """Lifespan startup/shutdown must not break /health/db when DB URL is unset."""
    empty_settings = MagicMock()
    empty_settings.supabase_db_url = ""
    with (
        patch("app.db.connection.get_settings", return_value=empty_settings),
        patch("app.main.get_settings", return_value=empty_settings),
        TestClient(app) as client,
    ):
        response = client.get("/health/db")
        assert response.status_code == 200
        assert response.json()["code"] == "db_unconfigured"
