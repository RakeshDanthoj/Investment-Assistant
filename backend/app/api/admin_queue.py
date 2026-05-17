"""Minimal editorial drafts queue API (Phase 1: no auth gate)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Query

from app.models.enums import EventCategory, LifecycleState
from app.models.schemas import EventRecord
from app.services.event_persistence import fetch_events_filtered

router = APIRouter(tags=["admin"])


def _row_to_schema(row: dict[str, Any]) -> EventRecord:
    cat = EventCategory(row["category"])
    state = LifecycleState(row["lifecycle_state"])
    event_uuid = UUID(str(row["id"]))
    ts = row.get("created_at")
    if isinstance(ts, str):
        created = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        if created.tzinfo is None:
            created = created.replace(tzinfo=UTC)
        else:
            created = created.astimezone(UTC)
    elif isinstance(ts, datetime):
        created = ts if ts.tzinfo else ts.replace(tzinfo=UTC)
    else:
        created = datetime.now(tz=UTC)

    return EventRecord(
        id=event_uuid,
        title=str(row["title"]),
        category=cat,
        source_url=str(row["source_url"]) if row.get("source_url") else None,
        canonical_url=str(row.get("canonical_url") or row.get("source_url") or ""),
        event_source=str(row.get("event_source") or ""),
        confidence_score=int(row["confidence_score"]),
        lifecycle_state=state,
        prompt_version=str(row["prompt_version"]) if row.get("prompt_version") else None,
        created_at=created,
    )


@router.get("/events", response_model=list[EventRecord])
def list_editorial_events(
    lifecycle_state: str | None = Query(default="draft"),
    category: EventCategory | None = None,
    event_source: str | None = None,
    limit: int = Query(default=200, ge=1, le=500),
) -> list[EventRecord]:
    rows = fetch_events_filtered(
        lifecycle_state=lifecycle_state,
        category=category.value if category else None,
        event_source=event_source,
        order_by_confidence_desc=True,
        limit=limit,
    )
    return [_row_to_schema(row) for row in rows]
