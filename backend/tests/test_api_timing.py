"""API timing headers and /health/db latency breakdown (P1.5-S1)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

_ORIGIN = "https://investment-assistant-frontend.vercel.app"


def _record_sample_db_timing(*, connect_ms: float, query_ms: float) -> dict[str, list]:
    from app.diagnostics.timing import record_db_connect, record_db_query

    record_db_connect(connect_ms)
    record_db_query(query_ms)
    return {"items": [], "meta": {}}


@patch("app.api.feed.build_feed_response")
def test_feed_includes_timing_headers(mock_build_feed: MagicMock) -> None:
    mock_build_feed.side_effect = lambda **_kwargs: _record_sample_db_timing(
        connect_ms=12.5,
        query_ms=3.2,
    )

    client = TestClient(app)
    response = client.get("/api/feed", headers={"Origin": _ORIGIN})

    assert response.status_code == 200
    assert "Server-Timing" in response.headers
    payload = json.loads(response.headers["X-FinnWise-Timing"])
    assert payload["db_connect_ms"] == 12.5
    assert payload["db_query_ms"] == 3.2
    assert payload["total_ms"] > 0


@patch("app.api.cards_detail.build_card_detail")
def test_card_detail_includes_timing_headers(mock_build_detail: MagicMock) -> None:
    def fake_build(_card_id, *, view: str) -> dict[str, str]:
        _record_sample_db_timing(connect_ms=20.0, query_ms=8.0)
        return {"id": "card-1", "title": "Test", "view": view}

    mock_build_detail.side_effect = fake_build

    client = TestClient(app)
    response = client.get(
        "/api/cards/00000000-0000-4000-8000-000000000001",
        headers={"Origin": _ORIGIN},
    )

    assert response.status_code == 200
    payload = json.loads(response.headers["X-FinnWise-Timing"])
    assert payload["db_connect_ms"] == 20.0
    assert payload["db_query_ms"] == 8.0


@patch("app.main.connection")
def test_health_db_returns_connect_and_query_breakdown(mock_connection: MagicMock) -> None:
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchone.return_value = (2,)
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_conn.cursor.return_value.__exit__.return_value = None
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = mock_conn
    mock_cm.__exit__.return_value = None

    def side_effect() -> MagicMock:
        from app.diagnostics.timing import record_db_connect, record_db_query

        record_db_connect(100.0)
        record_db_query(5.5)
        return mock_cm

    mock_connection.side_effect = side_effect

    client = TestClient(app)
    response = client.get("/health/db")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["cards"] == 2
    assert body["connect_ms"] == 100.0
    assert body["query_ms"] == 5.5
    assert body["total_ms"] > 0
