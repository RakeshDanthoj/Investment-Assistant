"""Reserve one NewsAPI call against the UTC daily quota (Postgres RPC via PostgREST)."""

from typing import Any

import httpx

from app.core.settings import get_settings, normalize_supabase_url

# Conservative ceiling so 4-hourly crons plus manual runs stay under NewsAPI free 100/day.
DEFAULT_NEWSAPI_DAILY_MAX = 95


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
    if isinstance(data, list) and len(data) == 1 and isinstance(data[0], dict):
        value = next(iter(data[0].values()), None)
        return bool(value)
    return False
