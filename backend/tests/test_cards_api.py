"""Cards API error mapping."""

from unittest.mock import patch
from uuid import uuid4

import httpx
from fastapi.testclient import TestClient
from openai import RateLimitError

from app.main import app
from app.services.llm_client import LlmTimeoutError

client = TestClient(app)


@patch("app.api.cards.draft_card_from_event")
def test_draft_from_event_maps_llm_quota_to_429(mock_draft) -> None:
    request = httpx.Request("POST", "https://integrate.api.nvidia.com/v1/chat/completions")
    response = httpx.Response(429, request=request)
    mock_draft.side_effect = RateLimitError("quota exceeded", response=response, body=None)

    res = client.post(
        "/api/cards/draft-from-event",
        json={"event_id": str(uuid4())},
    )

    assert res.status_code == 429
    body = res.json()
    assert body["detail"]["code"] == "llm_quota_exceeded"


@patch("app.api.cards.draft_card_from_event")
def test_draft_from_event_maps_llm_timeout_to_504(mock_draft) -> None:
    mock_draft.side_effect = LlmTimeoutError(timeout_seconds=120.0, prompt_version="synthesis.v1")

    res = client.post(
        "/api/cards/draft-from-event",
        json={"event_id": str(uuid4())},
    )

    assert res.status_code == 504
    body = res.json()
    assert body["detail"]["code"] == "llm_timeout"
    assert "timed out" in body["detail"]["message"].lower()
