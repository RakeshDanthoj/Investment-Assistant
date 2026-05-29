"""Reserve one NewsAPI call against the UTC daily quota (Postgres RPC via PostgREST)."""

from typing import Any

import httpx

from app.core.settings import get_settings, normalize_supabase_url

# Hard cap aligned with PRD2 §4.2 factor keyword budgets (100 calls/day total).
DEFAULT_NEWSAPI_DAILY_MAX = 100


def parse_newsapi_budget_rpc_response(data: object) -> bool | None:
    """
    Normalise PostgREST / Supabase RPC bodies for ``try_newsapi_call_budget``.

    Supabase commonly returns a bare JSON boolean; older clients expected a one-row object.
    """
    if isinstance(data, bool):
        return data
    if isinstance(data, dict) and data:
        return bool(next(iter(data.values())))
    if isinstance(data, list) and len(data) == 1:
        item = data[0]
        if isinstance(item, bool):
            return item
        if isinstance(item, dict) and item:
            return bool(next(iter(item.values())))
    return None


def reserve_news_api_call(*, ceiling: int = DEFAULT_NEWSAPI_DAILY_MAX) -> bool:
    """
    Reserve one successful budget slot immediately (returns False if quota exhausted).
    """
    settings = get_settings()
    base = normalize_supabase_url(settings.supabase_url.strip()).rstrip("/")
    key = settings.supabase_service_role_key.strip()
    if not base or not key:
        return False

    url = f"{base}/rest/v1/rpc/try_newsapi_call_budget"
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

    payload: dict[str, Any] = {"p_max": ceiling}
    with httpx.Client(timeout=15.0) as client:
        r = client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
    parsed = parse_newsapi_budget_rpc_response(data)
    return parsed if parsed is not None else False
