"""Persist onboarding outcome to Supabase (session-only amount is never stored)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import httpx

from app.core.settings import get_settings


def persist_session_profile(
    *,
    session_id: UUID,
    user_id: str | None,
    status: str,
    horizon: str,
    cadence: str,
    mode: str,
) -> bool:
    """
    Insert a row into session_profiles via PostgREST.
    Returns True if a row was written, False if Supabase is not configured (local dev).
    """
    settings = get_settings()
    base = settings.supabase_url.strip().rstrip("/")
    key = settings.supabase_service_role_key.strip()
    if not base or not key:
        return False

    payload: dict[str, Any] = {
        "session_id": str(session_id),
        "status": status,
        "horizon": horizon,
        "cadence": cadence,
        "mode": mode,
    }
    if user_id:
        payload["user_id"] = user_id

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }

    url = f"{base}/rest/v1/session_profiles"
    with httpx.Client(timeout=10.0) as client:
        r = client.post(url, headers=headers, json=payload)
        r.raise_for_status()
    return True
