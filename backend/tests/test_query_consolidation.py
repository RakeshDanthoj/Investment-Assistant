"""Single-connection feed and card-detail queries (P1.5-S3)."""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.diagnostics.timing import DbRequestTimer, record_db_connect, record_db_query
from app.services.bias_detector import build_bias_audit
from app.services.card_detail import build_card_detail
from app.services.feed import build_feed_response


@contextmanager
def _timed_mock_connection():
    record_db_connect(0.1)
    try:
        yield MagicMock()
    finally:
        record_db_query(0.5)


@patch("app.services.feed._fetch_fog_of_war_conn", return_value=False)
@patch("app.services.feed._fetch_pulse_rows_conn", return_value=([], None))
@patch("app.services.feed.connection")
def test_build_feed_uses_single_connection(
    mock_connection: MagicMock,
    mock_rows: MagicMock,
    mock_fog: MagicMock,
) -> None:
    mock_connection.side_effect = _timed_mock_connection

    with DbRequestTimer() as timer:
        build_feed_response(session_id=None, horizon=None, category=None)

    assert timer.snapshot()["connection_count"] == 1
    mock_rows.assert_called_once()
    mock_fog.assert_called_once()


def test_fetch_card_detail_bundle_uses_single_connection() -> None:
    from app.services.card_repository import fetch_card_detail_bundle

    card_id = uuid4()
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_cur.fetchone.side_effect = [
        {
            "card_id": str(card_id),
            "event_id": str(uuid4()),
            "title": "Test card",
            "insight_layer": "Insight",
            "context_layer": "Context",
            "evidence_layer": {},
            "dissenting_view": "",
            "framework_behind_this": "",
            "prompt_version": "pytest",
            "lifecycle_state": "published",
            "card_created_at": None,
            "event_title": "Event",
            "event_category": "macro",
            "event_confidence_score": 55,
            "event_lifecycle_state": "published",
            "event_canonical_url": None,
        },
    ]
    mock_cur.fetchall.return_value = []
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_conn.cursor.return_value.__exit__.return_value = None

    @contextmanager
    def conn_with_cursor():
        record_db_connect(0.1)
        try:
            yield mock_conn
        finally:
            record_db_query(0.5)

    with patch("app.services.card_repository.connection", conn_with_cursor):
        with DbRequestTimer() as timer:
            bundle = fetch_card_detail_bundle(card_id)

    assert bundle is not None
    assert timer.snapshot()["connection_count"] == 1
    assert mock_cur.execute.call_count == 4


@patch("app.services.card_detail.fetch_card_detail_bundle")
def test_build_card_detail_current_uses_bundle_not_piecemeal_fetches(
    mock_bundle: MagicMock,
) -> None:
    card_id = uuid4()
    mock_bundle.return_value = MagicMock(
        detail={
            "card_id": str(card_id),
            "event_id": str(uuid4()),
            "title": "Test card",
            "insight_layer": "Insight [MEASURED]",
            "context_layer": "1. Step [MEASURED]",
            "evidence_layer": {"markdown": "MD [MODELLED]", "sources": []},
            "dissenting_view": "Dissent [JUDGED]",
            "framework_behind_this": "Framework",
            "event_title": "Event",
            "event_category": "macro",
            "event_confidence_score": 55,
            "lifecycle_state": "published",
            "card_created_at": None,
        },
        signals=[],
        instruments=[],
        bias_flags=[],
    )

    payload = build_card_detail(card_id, view="current")

    assert payload is not None
    mock_bundle.assert_called_once_with(card_id)


@patch("app.services.bias_detector.fetch_bias_flag_rows")
def test_build_bias_audit_uses_prefetched_rows_without_db(mock_fetch: MagicMock) -> None:
    rows = [
        {
            "bias_type": "recency",
            "severity": "flagged",
            "description": "Recent sources dominate.",
        }
    ]
    audit = build_bias_audit(card_id=uuid4(), bias_rows=rows)
    mock_fetch.assert_not_called()
    assert len(audit["flags"]) == 1
    assert audit["flags"][0]["id"] == "recency"


def test_build_feed_live_connection_count(database_url: str) -> None:
    with DbRequestTimer() as timer:
        build_feed_response(session_id=None, horizon=None, category=None)

    assert timer.snapshot()["connection_count"] == 1


def test_build_card_detail_current_live_connection_count(database_url: str) -> None:
    import psycopg
    from psycopg.rows import dict_row

    card_id: UUID | None = None
    with psycopg.connect(database_url) as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT c.id::text AS id
            FROM public.cards c
            WHERE c.lifecycle_state::text IN (
              'published', 'active', 'signal_triggered',
              'thesis_confirmed', 'thesis_weakened', 'resolved'
            )
            ORDER BY c.created_at DESC
            LIMIT 1
            """
        )
        row = cur.fetchone()
        if not row:
            pytest.skip("No published card in database for integration test")
        card_id = UUID(row["id"])

    with DbRequestTimer() as timer:
        payload = build_card_detail(card_id, view="current")

    assert payload is not None
    assert timer.snapshot()["connection_count"] == 1
