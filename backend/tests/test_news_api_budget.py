"""NewsAPI daily budget RPC response parsing (P1-S6 / P3-S1d)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.services.news_api_budget import (
    parse_newsapi_budget_rpc_response,
    reserve_news_api_call,
)


def test_parse_bare_boolean_true() -> None:
    assert parse_newsapi_budget_rpc_response(True) is True


def test_parse_bare_boolean_false() -> None:
    assert parse_newsapi_budget_rpc_response(False) is False


def test_parse_wrapped_object() -> None:
    assert parse_newsapi_budget_rpc_response([{"try_newsapi_call_budget": True}]) is True


def test_reserve_news_api_call_accepts_bare_true_response() -> None:
    resp = MagicMock()
    resp.json.return_value = True
    resp.raise_for_status.return_value = None

    with (
        patch("app.services.news_api_budget.get_settings") as settings,
        patch("httpx.Client") as client_cls,
    ):
        settings.return_value.supabase_url = "https://proj.supabase.co"
        settings.return_value.supabase_service_role_key = "service-key"
        client_cls.return_value.__enter__.return_value.post.return_value = resp

        assert reserve_news_api_call(ceiling=100) is True
