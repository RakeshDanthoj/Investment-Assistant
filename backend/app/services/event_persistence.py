"""Supabase REST helpers for FinnWise editorial event queue (P1-S6)."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.settings import get_settings, normalize_supabase_url
from app.models.enums import EventCategory, LifecycleState
from app.sources.base import AdapterSource

_LOG = logging.getLogger(__name__)

EVENT_SELECT_FIELDS = (
    "id,title,category,source_url,canonical_url,event_source,"
    "confidence_score,lifecycle_state,prompt_version,created_at"
)


def persist_draft_event(
    *,
    title: str,
    category: EventCategory,
    event_source: AdapterSource | str,
    canonical_url: str,
    confidence_score: int,
    source_url: str | None = None,
) -> str:
    """
    Deduped insert: returns `inserted`, `skipped_no_config`, `duplicate`, or `error`.

    Dedupe enforced by Postgres unique `(event_source, canonical_url)`.
    """
    settings = get_settings()
    base = normalize_supabase_url(settings.supabase_url.strip()).rstrip("/")
    key = settings.supabase_service_role_key.strip()
    src = event_source.value if isinstance(event_source, AdapterSource) else event_source

    if not base or not key:
        return "skipped_no_config"

    canonical_url_norm = canonical_url.strip()
    if not canonical_url_norm:
        return "skipped_no_config"

    payload: dict[str, Any] = {
        "title": title[:3800],
        "category": category.value,
        "event_source": src,
        "canonical_url": canonical_url_norm[:3800],
        "source_url": (source_url or canonical_url_norm)[:3800],
        "confidence_score": confidence_score,
        "lifecycle_state": LifecycleState.DRAFT.value,
    }

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    url = f"{base}/rest/v1/events"

    try:
        with httpx.Client(timeout=20.0) as client:
            r = client.post(url, headers=headers, json=payload)
    except httpx.HTTPError as exc:
        _LOG.warning(
            "event_persistence.failed",
            extra={"event_source": src, "url": canonical_url_norm, "error": repr(exc)},
        )
        return "error"

    if _is_unique_violation_response(r.status_code, r.content):
        return "duplicate"

    try:
        r.raise_for_status()
    except httpx.HTTPStatusError as exc:
        _LOG.warning(
            "event_persistence.http_error",
            extra={
                "event_source": src,
                "url": canonical_url_norm,
                "status": r.status_code,
                "body": r.text[:500],
                "error": repr(exc),
            },
        )
        return "error"
    return "inserted"


def _is_unique_violation_response(status_code: int, body: bytes) -> bool:
    if status_code == 409:
        return True
    if status_code != 400:
        return False
    try:
        decoded = body.decode(errors="ignore")
    except Exception:
        decoded = ""
    return "duplicate key value" in decoded.lower()


def fetch_events_filtered(
    *,
    lifecycle_state: str | None = None,
    category: str | None = None,
    event_source: str | None = None,
    order_by_confidence_desc: bool = True,
    limit: int = 250,
) -> list[dict[str, Any]]:
    """Read events from Supabase via PostgREST (returns raw dict rows)."""
    settings = get_settings()
    base = normalize_supabase_url(settings.supabase_url.strip()).rstrip("/")
    key = settings.supabase_service_role_key.strip()

    if not base or not key:
        return []

    params: dict[str, str | int] = {
        "select": EVENT_SELECT_FIELDS,
        "limit": limit,
    }
    if lifecycle_state:
        params["lifecycle_state"] = f"eq.{lifecycle_state}"
    if category:
        params["category"] = f"eq.{category}"
    if event_source:
        params["event_source"] = f"eq.{event_source}"
    if order_by_confidence_desc:
        params["order"] = "confidence_score.desc"

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Accept": "application/json",
    }
    url = f"{base}/rest/v1/events"

    try:
        with httpx.Client(timeout=20.0) as client:
            r = client.get(url, headers=headers, params=params)
            r.raise_for_status()
            data = r.json()
    except (httpx.HTTPError, ValueError) as exc:
        _LOG.warning("event_fetch.failed", extra={"error": repr(exc)})
        return []

    if isinstance(data, list):
        return data
    return []
