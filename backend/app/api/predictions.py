"""Authenticated prediction logging for Thread Prediction Logger (P1-S12)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.auth import CurrentUser
from app.services.predictions import (
    DuplicatePredictionError,
    PredictionError,
    UserPredictionRow,
    list_for_user,
    log,
)

router = APIRouter()


class PredictionCreate(BaseModel):
    card_id: UUID
    prediction_text: str = Field(..., min_length=8, max_length=2000)


class PredictionCreateResponse(BaseModel):
    ok: bool = True


class UserPredictionItem(BaseModel):
    card_id: UUID
    prediction_text: str
    logged_at: datetime


class UserPredictionsResponse(BaseModel):
    items: list[UserPredictionItem]


def _row_to_item(row: UserPredictionRow) -> UserPredictionItem:
    return UserPredictionItem(
        card_id=row.card_id,
        prediction_text=row.prediction_text,
        logged_at=row.logged_at,
    )


def _raise_prediction_error(exc: PredictionError) -> None:
    msg = str(exc)
    if isinstance(exc, DuplicatePredictionError):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": msg,
                "message": "Prediction already logged for this card",
                "prediction_text": exc.prediction_text,
            },
        ) from exc
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


@router.post("/predictions", response_model=PredictionCreateResponse)
def post_prediction(body: PredictionCreate, current_user: CurrentUser) -> PredictionCreateResponse:
    try:
        log(
            user_id=UUID(current_user.id),
            card_id=body.card_id,
            prediction_text=body.prediction_text,
        )
    except PredictionError as exc:
        _raise_prediction_error(exc)
    except RuntimeError as exc:
        if "SUPABASE_DB_URL" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"code": "db_unavailable", "message": str(exc)},
            ) from exc
        raise
    return PredictionCreateResponse()


@router.get("/predictions/me", response_model=UserPredictionsResponse)
def get_my_predictions(current_user: CurrentUser, limit: int = 100) -> UserPredictionsResponse:
    try:
        rows = list_for_user(UUID(current_user.id), limit=limit)
    except RuntimeError as exc:
        if "SUPABASE_DB_URL" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"code": "db_unavailable", "message": str(exc)},
            ) from exc
        raise
    return UserPredictionsResponse(items=[_row_to_item(row) for row in rows])
