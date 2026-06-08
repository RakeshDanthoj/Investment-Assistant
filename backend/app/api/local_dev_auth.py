"""Localhost-only password sign-in for admin emails (development)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.services.local_dev_auth import (
    LocalDevAuthError,
    is_local_dev_browser_origin,
    local_dev_auth_enabled,
    local_dev_login,
)

router = APIRouter(tags=["auth"])


class LocalDevLoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=6, max_length=128)


class LocalDevLoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int | None = None
    token_type: str = "bearer"


@router.post("/local-dev-login", response_model=LocalDevLoginResponse)
async def post_local_dev_login(
    body: LocalDevLoginRequest,
    request: Request,
) -> LocalDevLoginResponse:
    if not local_dev_auth_enabled():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    origin = request.headers.get("origin")
    referer = request.headers.get("referer")
    if not is_local_dev_browser_origin(origin, referer):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    try:
        session = await local_dev_login(body.email, body.password)
    except LocalDevAuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    return LocalDevLoginResponse(**session)
