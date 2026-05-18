"""Admin editorial review API — inspect draft, publish, regenerate (Phase 1: no auth gate)."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.card_pipeline import DissentQualityError, FrameworkQualityError
from app.services.card_repository import (
    fetch_card_detail_for_review,
    fetch_instrument_assessments_for_card,
)
from app.services.cost_guard import DailyLLMCardCapError
from app.services.publish_card import PublishCardError, publish_draft_card
from app.services.regenerate_card import RegenerateCardError, regenerate_draft_with_notes

router = APIRouter(tags=["admin-cards"])


class PublishCardBody(BaseModel):
    editor_review_seconds: int | None = Field(default=None, ge=0, le=86400)


class RegenerateCardBody(BaseModel):
    editor_notes: str = Field(default="", max_length=8000)


def _serialize_detail(row: dict) -> dict:
    out = dict(row)
    out["card_id"] = str(out["card_id"])
    out["event_id"] = str(out["event_id"])
    ts = out.get("card_created_at")
    if isinstance(ts, datetime):
        out["card_created_at"] = ts.astimezone(UTC).isoformat()
    return out


@router.get("/cards/{card_id}")
def get_card_for_review(card_id: UUID) -> dict:
    row = fetch_card_detail_for_review(card_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "card_not_found", "message": str(card_id)},
        )
    payload = _serialize_detail(row)
    payload["instrument_assessments"] = fetch_instrument_assessments_for_card(card_id)
    return payload


@router.post("/cards/{card_id}/publish")
def post_publish_card(card_id: UUID, body: PublishCardBody) -> dict:
    try:
        return publish_draft_card(card_id, editor_review_seconds=body.editor_review_seconds)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "card_not_found", "message": str(exc)},
        ) from exc
    except PublishCardError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "publish_rejected", "message": str(exc)},
        ) from exc


@router.post("/cards/{card_id}/regenerate")
def post_regenerate_card(card_id: UUID, body: RegenerateCardBody) -> dict:
    try:
        new_id = regenerate_draft_with_notes(card_id, body.editor_notes)
        return {"card_id": str(new_id)}
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "card_not_found", "message": str(exc)},
        ) from exc
    except RegenerateCardError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "regenerate_rejected", "message": str(exc)},
        ) from exc
    except DailyLLMCardCapError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": "llm_daily_cap", "message": str(exc)},
        ) from exc
    except (DissentQualityError, FrameworkQualityError, RuntimeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "draft_pipeline_failed", "message": str(exc)},
        ) from exc
