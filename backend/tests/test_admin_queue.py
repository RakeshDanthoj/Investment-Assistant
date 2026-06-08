"""Admin editorial queue API — draft card linkage on list events."""

from __future__ import annotations

from unittest.mock import patch
from uuid import UUID

from fastapi.testclient import TestClient

from app.main import app

EVENT_ID = UUID("11111111-1111-4111-8111-111111111111")
CARD_ID = UUID("22222222-2222-4222-8222-222222222222")


@patch("app.api.admin_queue.fetch_latest_draft_card_ids_by_event_ids")
@patch("app.api.admin_queue.fetch_events_filtered")
def test_list_editorial_events_includes_draft_card_id(mock_fetch_events, mock_fetch_cards):
    mock_fetch_events.return_value = [
        {
            "id": str(EVENT_ID),
            "title": "RBI holds repo",
            "category": "rbi_policy",
            "source_url": "https://example.com/rbi",
            "canonical_url": "https://example.com/rbi",
            "event_source": "rbi_rss",
            "confidence_score": 80,
            "lifecycle_state": "draft",
            "prompt_version": None,
            "created_at": "2026-05-22T10:00:00+00:00",
        }
    ]
    mock_fetch_cards.return_value = {EVENT_ID: CARD_ID}

    client = TestClient(app)
    response = client.get("/admin/events?lifecycle_state=draft")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == str(EVENT_ID)
    assert payload[0]["draft_card_id"] == str(CARD_ID)
