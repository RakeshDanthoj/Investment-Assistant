"""Admin aggregate metrics endpoint (P2-S13)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.core.admin_emails import normalized_admin_emails
from app.core.auth import User, get_current_user
from app.core.settings import get_settings
from app.services.admin_metrics import fetch_admin_metrics

router = APIRouter(tags=["admin-metrics"])


def require_admin(current: User = Depends(get_current_user)) -> User:
    allow = normalized_admin_emails(get_settings())
    email = (current.email or "").strip().lower()
    if not allow or email not in allow:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin metrics access denied",
        )
    return current


class AdminMetricsResponse(BaseModel):
    as_of: str
    window_days: int
    daily_card_count: int
    p95_generation_time_ms: float | None
    high_confidence_override_rate: float | None
    signal_false_positive_rate: float | None
    high_confidence_gate_total: int
    high_confidence_gate_overridden: int


@router.get("/metrics", response_model=AdminMetricsResponse)
def get_admin_metrics(
    window_days: int = Query(default=30, ge=1, le=365),
    _: User = Depends(require_admin),
) -> AdminMetricsResponse:
    try:
        payload = fetch_admin_metrics(window_days=window_days)
    except RuntimeError as exc:
        if "SUPABASE_DB_URL" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={"code": "db_unavailable", "message": str(exc)},
            ) from exc
        raise
    return AdminMetricsResponse(**payload)
