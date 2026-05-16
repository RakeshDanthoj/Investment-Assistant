from typing import Annotated

import httpx
from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel

from app.core.settings import get_settings, normalize_supabase_url


class User(BaseModel):
    id: str
    email: str | None = None
    role: str | None = None
    user_metadata: dict = {}


async def verify_supabase_token(token: str) -> User:
    settings = get_settings()
    base_url = normalize_supabase_url(settings.supabase_url)
    if not base_url or not settings.supabase_anon_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Auth is not configured",
        )

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{base_url}/auth/v1/user",
            headers={
                "apikey": settings.supabase_anon_key,
                "Authorization": f"Bearer {token}",
            },
            timeout=10.0,
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    payload = response.json()
    return User(
        id=payload["id"],
        email=payload.get("email"),
        role=payload.get("role"),
        user_metadata=payload.get("user_metadata") or {},
    )


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    return await verify_supabase_token(token)


CurrentUser = Annotated[User, Depends(get_current_user)]
