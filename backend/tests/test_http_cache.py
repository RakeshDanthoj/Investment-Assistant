"""HTTP Cache-Control headers for published read paths (P1.5-S4)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.http.cache_control import NO_STORE_CACHE, PUBLIC_FEED_CACHE, PUBLISHED_READ_CACHE
from app.main import app

_ORIGIN = "https://investment-assistant-frontend.vercel.app"
_CARD_ID = "00000000-0000-4000-8000-000000000001"


def _sample_feed_payload() -> dict[str, object]:
    return {"items": [], "meta": {"fog_of_war": False}}


def _sample_card_payload(*, lifecycle_state: str = "published") -> dict[str, str]:
    return {
        "card_id": _CARD_ID,
        "title": "Test card",
        "lifecycle_state": lifecycle_state,
        "view": "current",
    }


@patch("app.api.feed.build_feed_response")
def test_feed_sets_public_cache_control_when_anonymous(mock_build_feed: MagicMock) -> None:
    mock_build_feed.return_value = _sample_feed_payload()

    client = TestClient(app)
    response = client.get("/api/feed", headers={"Origin": _ORIGIN})

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == PUBLIC_FEED_CACHE


@patch("app.api.feed.build_feed_response")
def test_feed_sets_private_cache_control_with_personalisation_token(
    mock_build_feed: MagicMock,
) -> None:
    mock_build_feed.return_value = _sample_feed_payload()

    client = TestClient(app)
    response = client.get(
        "/api/feed",
        params={"personalisation_token": "opaque-token"},
        headers={"Origin": _ORIGIN},
    )

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == PUBLISHED_READ_CACHE


@patch("app.api.feed.build_feed_response")
def test_feed_sets_private_cache_control_with_session_id(mock_build_feed: MagicMock) -> None:
    mock_build_feed.return_value = _sample_feed_payload()

    client = TestClient(app)
    response = client.get(
        "/api/feed",
        params={"session_id": "00000000-0000-4000-8000-000000000099"},
        headers={"Origin": _ORIGIN},
    )

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == PUBLISHED_READ_CACHE


@patch("app.api.cards_detail.build_card_detail")
def test_card_detail_current_published_is_cacheable(mock_build_detail: MagicMock) -> None:
    mock_build_detail.return_value = _sample_card_payload(lifecycle_state="active")

    client = TestClient(app)
    response = client.get(f"/api/cards/{_CARD_ID}", headers={"Origin": _ORIGIN})

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == PUBLISHED_READ_CACHE


@patch("app.api.cards_detail.build_card_detail")
def test_card_detail_current_draft_is_no_store(mock_build_detail: MagicMock) -> None:
    mock_build_detail.return_value = _sample_card_payload(lifecycle_state="draft")

    client = TestClient(app)
    response = client.get(f"/api/cards/{_CARD_ID}", headers={"Origin": _ORIGIN})

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == NO_STORE_CACHE


@patch("app.api.cards_detail.build_card_detail")
def test_card_detail_original_view_is_cacheable(mock_build_detail: MagicMock) -> None:
    payload = _sample_card_payload(lifecycle_state="published")
    payload["view"] = "original"
    mock_build_detail.return_value = payload

    client = TestClient(app)
    response = client.get(
        f"/api/cards/{_CARD_ID}",
        params={"view": "original"},
        headers={"Origin": _ORIGIN},
    )

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == PUBLISHED_READ_CACHE


@patch("app.api.cards_detail.build_card_detail")
def test_card_detail_not_found_is_no_store(mock_build_detail: MagicMock) -> None:
    mock_build_detail.return_value = None

    client = TestClient(app)
    response = client.get(f"/api/cards/{_CARD_ID}", headers={"Origin": _ORIGIN})

    assert response.status_code == 404
    assert response.headers["Cache-Control"] == NO_STORE_CACHE


@patch("app.api.admin_review.fetch_card_detail_for_review")
@patch("app.api.admin_review.fetch_instrument_assessments_for_card")
def test_admin_card_review_is_no_store(
    mock_instruments: MagicMock,
    mock_fetch: MagicMock,
) -> None:
    mock_fetch.return_value = {
        "card_id": _CARD_ID,
        "event_id": "00000000-0000-4000-8000-000000000002",
        "title": "Draft card",
        "lifecycle_state": "draft",
        "card_created_at": None,
    }
    mock_instruments.return_value = []

    client = TestClient(app)
    response = client.get(f"/api/admin/cards/{_CARD_ID}", headers={"Origin": _ORIGIN})

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == NO_STORE_CACHE


@patch("app.api.feed.build_feed_response")
def test_feed_cache_header_is_stable_on_repeat_requests(mock_build_feed: MagicMock) -> None:
    mock_build_feed.return_value = _sample_feed_payload()

    client = TestClient(app)
    first = client.get("/api/feed", headers={"Origin": _ORIGIN})
    second = client.get("/api/feed", headers={"Origin": _ORIGIN})

    assert first.headers["Cache-Control"] == PUBLIC_FEED_CACHE
    assert second.headers["Cache-Control"] == PUBLIC_FEED_CACHE
    assert mock_build_feed.call_count == 2
