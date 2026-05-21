from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from app.main import app


def test_onboarding_session_returns_502_with_cors_when_supabase_rejects() -> None:
    response = httpx.Response(
        401,
        request=httpx.Request("POST", "https://example.supabase.co/rest/v1/session_profiles"),
        text='{"message":"row-level security"}',
    )
    client = TestClient(app, raise_server_exceptions=False)

    with patch(
        "app.api.onboarding.persist_session_profile",
        side_effect=httpx.HTTPStatusError("Unauthorized", request=response.request, response=response),
    ):
        res = client.post(
            "/onboarding/session",
            json={
                "investment_status": "starting_fresh",
                "horizon": "1_3y",
                "cadence": "monthly",
            },
            headers={"Origin": "https://investment-assistant-frontend.vercel.app"},
        )

    assert res.status_code == 502
    assert "SUPABASE_SERVICE_ROLE_KEY" in res.text
    assert res.headers.get("access-control-allow-origin") == (
        "https://investment-assistant-frontend.vercel.app"
    )
