"""Confidence breakdown API contract — P3-S1g / P3-T3 shape and 404."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.db.migrate import apply_migrations
from app.main import app


@pytest.fixture(scope="module", autouse=True)
def ensure_migrations(db_connection):
    apply_migrations(db_connection)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_confidence_breakdown_shape(client: TestClient, db_connection) -> None:
    event_id = uuid4()
    canon = f"pytest:confidence-breakdown:{uuid4()}@invalid"
    ref = datetime(2025, 6, 1, 10, 0, tzinfo=UTC)
    try:
        with db_connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.events (
                  id, title, category, confidence_score, lifecycle_state,
                  canonical_url, event_source, source_count, sources,
                  confidence_raw, confidence_effective, factor_db_match_count
                )
                VALUES (
                  %s, %s, 'rbi_policy'::event_category, 88, 'draft',
                  %s, 'rbi_rss', 2, %s::jsonb,
                  0.82, 0.82, 2
                )
                """,
                (
                    str(event_id),
                    "RBI MPC repo unchanged — pytest",
                    canon,
                    '[{"event_source":"rbi_rss","canonical_url":"'
                    + canon
                    + '","retrieved_at":"'
                    + ref.isoformat()
                    + '"}]',
                ),
            )
        db_connection.commit()

        resp = client.get(f"/api/events/{event_id}/confidence-breakdown")
        assert resp.status_code == 200
        body = resp.json()
        assert body["confidence_raw"] == pytest.approx(0.82, abs=0.15)
        assert body["tier"] in ("high", "medium", "low")
        assert "inputs" in body
        assert "source_count" in body["inputs"]
        assert "sources" in body
        assert body["scorer_version"]
        assert "Cache-Control" in resp.headers
        assert "max-age=60" in resp.headers["Cache-Control"]
    finally:
        with db_connection.cursor() as cur:
            cur.execute("DELETE FROM public.events WHERE id = %s", (str(event_id),))
        db_connection.commit()


def test_confidence_breakdown_not_found(client: TestClient) -> None:
    missing = uuid4()
    resp = client.get(f"/api/events/{missing}/confidence-breakdown")
    assert resp.status_code == 404
