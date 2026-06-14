from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from openai import APIStatusError, RateLimitError
from pydantic import BaseModel, Field

from app.api.admin_review import (
    RegenerateFullBody,
    RegenerateSectionBody,
    post_regenerate_full,
    post_regenerate_section,
)
from app.services.card_pipeline import (
    CriticalFactsHoldError,
    DissentQualityError,
    FrameworkQualityError,
    draft_card_from_event,
)
from app.services.cost_guard import DailyLLMCardCapError, MonthlyLLMBudgetError
from app.services.llm_client import LlmTimeoutError

router = APIRouter()


class DraftFromEventRequest(BaseModel):
    event_id: UUID
    editor_notes: str | None = Field(default=None, max_length=8000)


class DraftFromEventResponse(BaseModel):
    card_id: UUID


@router.post("/draft-from-event", response_model=DraftFromEventResponse)
def post_draft_from_event(body: DraftFromEventRequest) -> DraftFromEventResponse:
    try:
        card_id = draft_card_from_event(body.event_id, editor_notes=body.editor_notes)
    except DailyLLMCardCapError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": "llm_daily_cap", "message": str(exc)},
        ) from exc
    except MonthlyLLMBudgetError as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={"code": "llm_monthly_budget", "message": str(exc)},
        ) from exc
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "event_not_found", "message": str(exc)},
        ) from exc
    except CriticalFactsHoldError as exc:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail={
                "code": "critical_facts_held",
                "message": str(exc),
                "unavailable_critical_facts": list(exc.unavailable_fact_ids),
            },
        ) from exc
    except LlmTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={"code": "llm_timeout", "message": str(exc)},
        ) from exc
    except RateLimitError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "llm_quota_exceeded",
                "message": (
                    "NVIDIA API quota exceeded. Wait a minute and retry, or check "
                    "credits and rate limits at build.nvidia.com."
                ),
            },
        ) from exc
    except APIStatusError as exc:
        if exc.status_code == 429:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "llm_quota_exceeded",
                    "message": (
                        "NVIDIA API quota exceeded. Wait a minute and retry, or check "
                        "credits and rate limits at build.nvidia.com."
                    ),
                },
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"code": "llm_provider_error", "message": str(exc)},
        ) from exc
    except (DissentQualityError, FrameworkQualityError, ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "draft_pipeline_failed", "message": str(exc)},
        ) from exc

    return DraftFromEventResponse(card_id=card_id)


@router.post("/{card_id}/regenerate-section")
def post_card_regenerate_section(card_id: UUID, body: RegenerateSectionBody) -> dict:
    return post_regenerate_section(card_id, body)


@router.post("/{card_id}/regenerate-full")
def post_card_regenerate_full(card_id: UUID, body: RegenerateFullBody) -> dict:
    return post_regenerate_full(card_id, body)
