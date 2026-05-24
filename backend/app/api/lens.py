"""The Lens — on-demand query input and history (P2-S6)."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.core.auth import CurrentUser
from app.middleware.rate_limit import (
    LensDailyRateLimitError,
    enforce_lens_daily_limit,
    lens_rate_limit_http_exception,
)
from app.services.cost_guard import MonthlyLLMBudgetError, check_monthly_budget_or_raise
from app.services.lens_queries import (
    LensQueryRow,
    LensQueryStatus,
    create_query,
    enqueue_generation,
    list_recent_for_user,
)

router = APIRouter(prefix="/lens", tags=["lens"])

HorizonValue = Literal["under_1y", "1_3y", "3_7y", "7_plus"]
SectorValue = Literal[
    "macro",
    "rbi_policy",
    "regulatory",
    "india_specific",
    "geopolitical",
    "budget",
]


class LensQueryCreate(BaseModel):
    query: str = Field(..., min_length=11, max_length=4000)
    sector: SectorValue | None = None
    horizon: HorizonValue | None = None


class LensQueryItem(BaseModel):
    id: UUID
    query: str
    sector: str | None
    horizon: str | None
    status: LensQueryStatus
    card_id: UUID | None
    created_at: datetime


class LensQueryCreateResponse(BaseModel):
    id: UUID
    status: LensQueryStatus


class LensQueriesListResponse(BaseModel):
    items: list[LensQueryItem]


def _row_to_item(row: LensQueryRow) -> LensQueryItem:
    return LensQueryItem(
        id=row.id,
        query=row.query,
        sector=row.sector,
        horizon=row.horizon,
        status=row.status,
        card_id=row.card_id,
        created_at=row.created_at,
    )


def _db_unavailable(exc: RuntimeError) -> None:
    if "SUPABASE_DB_URL" in str(exc):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "db_unavailable", "message": str(exc)},
        ) from exc
    raise exc


def _validation_error(exc: ValueError) -> None:
    msg = str(exc)
    if msg == "query_too_short":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": msg, "message": "Query must exceed 10 characters"},
        ) from exc
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={"code": "invalid_query", "message": msg},
    ) from exc


@router.post(
    "/queries",
    response_model=LensQueryCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_lens_query(
    body: LensQueryCreate,
    current_user: CurrentUser,
) -> LensQueryCreateResponse:
    try:
        enforce_lens_daily_limit(user_id=UUID(current_user.id))
    except LensDailyRateLimitError as exc:
        raise lens_rate_limit_http_exception(exc) from exc
    except RuntimeError as exc:
        _db_unavailable(exc)

    try:
        check_monthly_budget_or_raise()
    except MonthlyLLMBudgetError as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={"code": "llm_monthly_budget", "message": str(exc)},
        ) from exc
    except RuntimeError as exc:
        _db_unavailable(exc)

    try:
        row = create_query(
            user_id=UUID(current_user.id),
            query=body.query,
            sector=body.sector,
            horizon=body.horizon,
        )
        enqueue_generation(row.id)
    except ValueError as exc:
        _validation_error(exc)
    except RuntimeError as exc:
        _db_unavailable(exc)
    return LensQueryCreateResponse(id=row.id, status=row.status)


@router.get("/queries/me", response_model=LensQueriesListResponse)
def get_my_lens_queries(current_user: CurrentUser) -> LensQueriesListResponse:
    try:
        rows = list_recent_for_user(UUID(current_user.id))
    except RuntimeError as exc:
        _db_unavailable(exc)
    return LensQueriesListResponse(items=[_row_to_item(row) for row in rows])
