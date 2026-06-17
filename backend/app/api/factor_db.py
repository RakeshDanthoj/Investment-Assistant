"""HTTP surface for Factor Exposure DB (P1-S5)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.admin_emails import normalized_admin_emails
from app.core.auth import User, get_current_user
from app.core.settings import get_settings
from app.services import factor_db as factor_db_svc

router = APIRouter(prefix="/factor-db")

def require_factor_db_admin(current: User = Depends(get_current_user)) -> User:
    allow = normalized_admin_emails(get_settings())
    email = (current.email or "").strip().lower()
    if not allow or email not in allow:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Factor DB admin access denied",
        )
    return current


class SensitivityResponse(BaseModel):
    instrument_ticker: str
    factor_slug: str
    instrument_display_name: str
    sensitivity: int = Field(ge=-5, le=5)
    mmj_tag: str
    source_url: str
    retrieved_at: datetime
    freshness: factor_db_svc.FreshnessTone


class MatrixResponse(BaseModel):
    sector: dict
    factors: list[dict]
    instruments: list[dict]
    sensitivities: dict[str, dict[str, dict]]


@router.get("/sensitivity", response_model=SensitivityResponse)
def get_sensitivity(
    instrument: str = Query(..., min_length=1),
    factor: str = Query(..., min_length=1),
    _: User = Depends(get_current_user),
) -> SensitivityResponse:
    try:
        row = factor_db_svc.lookup_sensitivity(
            instrument_ticker=instrument,
            factor_slug=factor,
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not configured",
        ) from None

    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sensitivity not found")

    return SensitivityResponse(
        instrument_ticker=row.ticker,
        factor_slug=row.factor_slug,
        instrument_display_name=row.instrument_display_name,
        sensitivity=row.sensitivity,
        mmj_tag=row.mmj_tag,
        source_url=row.source_url,
        retrieved_at=row.retrieved_at,
        freshness=row.freshness,
    )


@router.get("/matrix", response_model=MatrixResponse)
def get_matrix(
    sector: str = Query("banking", min_length=1),
    _: User = Depends(require_factor_db_admin),
) -> MatrixResponse:
    slug = sector.strip().lower()
    try:
        data = factor_db_svc.fetch_matrix_rows(sector_slug=slug)
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not configured",
        ) from None
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return MatrixResponse(**data)
