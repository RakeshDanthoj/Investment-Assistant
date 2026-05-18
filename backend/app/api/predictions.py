"""Minimal predictions endpoint for Thread Prediction Logger (P1-S10; hardened in P1-S12)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.prediction_log import PredictionLogError, log_prediction

router = APIRouter()


class PredictionCreate(BaseModel):
    card_id: UUID
    prediction_text: str = Field(..., min_length=8, max_length=2000)
    user_id: UUID = Field(
        ...,
        description="Authenticated user id; wired to auth provider in P1-S12.",
    )


class PredictionCreateResponse(BaseModel):
    ok: bool = True


@router.post("/predictions", response_model=PredictionCreateResponse)
def post_prediction(body: PredictionCreate) -> PredictionCreateResponse:
    try:
        log_prediction(
            user_id=body.user_id,
            card_id=body.card_id,
            prediction_text=body.prediction_text,
        )
    except PredictionLogError as exc:
        msg = str(exc)
        if msg == "card_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": msg, "message": "Unknown card id"},
            ) from exc
        if msg == "duplicate_prediction":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": msg, "message": "Prediction already logged for this card"},
            ) from exc
        if msg == "user_or_card_invalid":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": msg, "message": "Unknown user or card for prediction logging"},
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": msg, "message": msg},
        ) from exc
    except RuntimeError as exc:
        if "SUPABASE_DB_URL" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"code": "db_unavailable", "message": str(exc)},
            ) from exc
        raise
    return PredictionCreateResponse()
