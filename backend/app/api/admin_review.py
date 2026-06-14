"""Admin editorial review API — inspect draft, publish, regenerate (Phase 1: no auth gate)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.card_pipeline import DissentQualityError, FrameworkQualityError
from app.services.card_regen import (
    CardRegenError,
    FullRegenBlockedError,
    FullRegenConfirmRequiredError,
    regenerate_full,
    regenerate_section,
)
from app.services.card_repository import (
    fetch_card_detail_for_review,
    fetch_instrument_assessments_for_card,
)
from app.services.consistency_check import SectionKey
from app.services.cost_guard import DailyLLMCardCapError, MonthlyLLMBudgetError
from app.services.editorial_checklist import (
    EditorialChecklistFailedError,
)
from app.services.editorial_checklist import (
    check_card as check_editorial,
)
from app.services.llm_client import LlmTimeoutError
from app.services.number_validator import (
    NumberValidationFailedError,
    check_card,
)
from app.services.publish_card import PublishCardError, publish_draft_card
from app.services.regenerate_card import RegenerateCardError, regenerate_draft_with_notes

router = APIRouter(tags=["admin-cards"])


class PublishCardBody(BaseModel):
    editor_review_seconds: int | None = Field(default=None, ge=0, le=86400)
    plain_english_confirmed: bool = False


class RegenerateCardBody(BaseModel):
    editor_notes: str = Field(default="", max_length=8000)


class RegenerateSectionBody(BaseModel):
    section: SectionKey
    editor_note: str = Field(default="", max_length=500)


class RegenerateFullBody(BaseModel):
    editor_notes: str = Field(default="", max_length=8000)
    confirmed: bool = False


def _serialize_regen_result(result) -> dict:
    return {
        "card_id": str(result.card_id),
        "number_validation": result.post_check.number_validation.to_dict(),
        "consistency_check": result.post_check.consistency_check,
    }


def _serialize_detail(row: dict) -> dict:
    out = dict(row)
    out["card_id"] = str(out["card_id"])
    out["event_id"] = str(out["event_id"])
    ts = out.get("card_created_at")
    if isinstance(ts, datetime):
        out["card_created_at"] = ts.astimezone(UTC).isoformat()
    history = out.get("regen_history")
    if isinstance(history, str):
        try:
            out["regen_history"] = json.loads(history) if history.strip() else []
        except json.JSONDecodeError:
            out["regen_history"] = []
    elif history is None:
        out["regen_history"] = []
    out["full_regen_count"] = int(out.get("full_regen_count") or 0)
    out["po_regen_flag_cleared"] = bool(out.get("po_regen_flag_cleared"))
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
    payload["number_validation"] = check_card(payload).to_dict()
    payload["editorial_checklist"] = check_editorial(payload).to_dict()
    return payload


@router.post("/cards/{card_id}/publish")
def post_publish_card(card_id: UUID, body: PublishCardBody) -> dict:
    try:
        return publish_draft_card(
            card_id,
            editor_review_seconds=body.editor_review_seconds,
            plain_english_confirmed=body.plain_english_confirmed,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "card_not_found", "message": str(exc)},
        ) from exc
    except NumberValidationFailedError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "number_validator_failed",
                "message": "number validator failed",
                **exc.result.to_dict(),
            },
        ) from exc
    except EditorialChecklistFailedError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "code": "editorial_checklist_failed",
                "message": "editorial checklist failed",
                **exc.result.to_dict(),
            },
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
    except MonthlyLLMBudgetError as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={"code": "llm_monthly_budget", "message": str(exc)},
        ) from exc
    except LlmTimeoutError as exc:
        raise _llm_timeout_error(exc) from exc
    except (DissentQualityError, FrameworkQualityError, RuntimeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "draft_pipeline_failed", "message": str(exc)},
        ) from exc


def _regen_budget_errors(exc: BaseException) -> HTTPException:
    if isinstance(exc, DailyLLMCardCapError):
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": "llm_daily_cap", "message": str(exc)},
        )
    if isinstance(exc, MonthlyLLMBudgetError):
        return HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={"code": "llm_monthly_budget", "message": str(exc)},
        )
    raise exc


def _llm_timeout_error(exc: LlmTimeoutError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        detail={"code": "llm_timeout", "message": str(exc)},
    )


@router.post("/cards/{card_id}/regenerate-section")
def post_regenerate_section(card_id: UUID, body: RegenerateSectionBody) -> dict:
    try:
        result = regenerate_section(
            card_id,
            section=body.section,
            editor_note=body.editor_note,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "card_not_found", "message": str(exc)},
        ) from exc
    except CardRegenError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "regen_rejected", "message": str(exc)},
        ) from exc
    except (DailyLLMCardCapError, MonthlyLLMBudgetError) as exc:
        raise _regen_budget_errors(exc) from exc
    except LlmTimeoutError as exc:
        raise _llm_timeout_error(exc) from exc
    except (DissentQualityError, FrameworkQualityError, RuntimeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "regen_pipeline_failed", "message": str(exc)},
        ) from exc

    payload = _serialize_regen_result(result)
    payload["section"] = result.section
    payload["previous_hash"] = result.previous_hash
    payload["new_hash"] = result.new_hash
    return payload


@router.post("/cards/{card_id}/regenerate-full")
def post_regenerate_full(card_id: UUID, body: RegenerateFullBody) -> dict:
    try:
        result = regenerate_full(
            card_id,
            editor_notes=body.editor_notes,
            confirmed=body.confirmed,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "card_not_found", "message": str(exc)},
        ) from exc
    except FullRegenConfirmRequiredError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "full_regen_confirm_required",
                "message": str(exc),
                "full_regen_count": int(
                    (fetch_card_detail_for_review(card_id) or {}).get("full_regen_count") or 0
                ),
            },
        ) from exc
    except FullRegenBlockedError as exc:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail={"code": "full_regen_blocked", "message": str(exc)},
        ) from exc
    except CardRegenError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "regen_rejected", "message": str(exc)},
        ) from exc
    except (DailyLLMCardCapError, MonthlyLLMBudgetError) as exc:
        raise _regen_budget_errors(exc) from exc
    except LlmTimeoutError as exc:
        raise _llm_timeout_error(exc) from exc
    except (DissentQualityError, FrameworkQualityError, RuntimeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "regen_pipeline_failed", "message": str(exc)},
        ) from exc

    payload = _serialize_regen_result(result)
    payload["full_regen_count"] = result.full_regen_count
    return payload
