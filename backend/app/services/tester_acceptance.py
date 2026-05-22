"""Record and query mandatory tester briefing acceptance (P1-S14)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from app.core.settings import get_settings, normalize_supabase_url


class TesterAcceptanceError(Exception):
    pass


def _rest_headers(service_key: str) -> dict[str, str]:
    return {
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json",
    }


def _base_rest_url() -> tuple[str, str] | None:
    settings = get_settings()
    base = normalize_supabase_url(settings.supabase_url)
    key = settings.supabase_service_role_key.strip()
    if not base or not key:
        return None
    return base, key


def has_accepted(user_id: str) -> bool:
    """Return True when the user has a tester_acceptances row."""
    cfg = _base_rest_url()
    if cfg is None:
        return False
    base, key = cfg
    url = f"{base}/rest/v1/tester_acceptances"
    params = {
        "select": "user_id",
        "user_id": f"eq.{user_id}",
        "limit": "1",
    }
    with httpx.Client(timeout=10.0) as client:
        response = client.get(url, headers=_rest_headers(key), params=params)
        response.raise_for_status()
        rows = response.json()
    return bool(rows)


def record_acceptance(*, user_id: str, ip: str | None) -> datetime:
    """
    Insert acceptance row for user. Raises TesterAcceptanceError on duplicate.
    Returns accepted_at from the stored row.
    """
    cfg = _base_rest_url()
    if cfg is None:
        raise TesterAcceptanceError("supabase_not_configured")
    base, key = cfg

    payload: dict[str, Any] = {"user_id": user_id}
    if ip:
        payload["ip"] = ip

    url = f"{base}/rest/v1/tester_acceptances"
    headers = {
        **_rest_headers(key),
        "Prefer": "return=representation",
    }
    with httpx.Client(timeout=10.0) as client:
        response = client.post(url, headers=headers, json=payload)
        if response.status_code == 409:
            raise TesterAcceptanceError("already_accepted")
        response.raise_for_status()
        rows = response.json()

    if not rows:
        raise TesterAcceptanceError("insert_failed")
    accepted_at_raw = rows[0].get("accepted_at")
    if not accepted_at_raw:
        return datetime.utcnow()
    return datetime.fromisoformat(accepted_at_raw.replace("Z", "+00:00"))
