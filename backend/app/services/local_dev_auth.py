"""Localhost-only admin sign-in using env-configured credentials."""

from __future__ import annotations

import secrets
from typing import Any

import httpx

from app.core.admin_emails import normalized_admin_emails
from app.core.settings import get_settings, normalize_supabase_url

_LOCALHOST_ORIGINS = frozenset(
    {
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    }
)

INVALID_CREDENTIALS = "Invalid email or password"


class LocalDevAuthError(Exception):
    def __init__(self, detail: str, status_code: int) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


def local_dev_auth_enabled() -> bool:
    settings = get_settings()
    return bool(
        settings.local_dev_password.strip()
        and settings.supabase_service_role_key.strip()
        and settings.supabase_anon_key.strip()
        and settings.supabase_url.strip()
    )


def is_local_dev_browser_origin(origin: str | None, referer: str | None) -> bool:
    for value in (origin, referer):
        if not value:
            continue
        for allowed in _LOCALHOST_ORIGINS:
            if value.startswith(allowed):
                return True
    return False


def _admin_headers(service_role_key: str) -> dict[str, str]:
    return {
        "apikey": service_role_key,
        "Authorization": f"Bearer {service_role_key}",
        "Content-Type": "application/json",
    }


async def _find_user_id_by_email(
    client: httpx.AsyncClient,
    base_url: str,
    service_role_key: str,
    email: str,
) -> str | None:
    page = 1
    while page <= 10:
        response = await client.get(
            f"{base_url}/auth/v1/admin/users",
            params={"page": page, "per_page": 100},
            headers=_admin_headers(service_role_key),
            timeout=15.0,
        )
        if response.status_code != 200:
            return None
        payload = response.json()
        users = payload.get("users") if isinstance(payload, dict) else None
        if not isinstance(users, list):
            return None
        for user in users:
            if not isinstance(user, dict):
                continue
            user_email = (user.get("email") or "").strip().lower()
            if user_email == email:
                user_id = user.get("id")
                if isinstance(user_id, str) and user_id:
                    return user_id
        if len(users) < 100:
            break
        page += 1
    return None


async def _ensure_auth_user(
    client: httpx.AsyncClient,
    base_url: str,
    service_role_key: str,
    email: str,
    password: str,
) -> None:
    create_response = await client.post(
        f"{base_url}/auth/v1/admin/users",
        json={
            "email": email,
            "password": password,
            "email_confirm": True,
        },
        headers=_admin_headers(service_role_key),
        timeout=15.0,
    )
    if create_response.status_code in (200, 201):
        return

    if create_response.status_code not in (409, 422):
        create_response.raise_for_status()

    user_id = await _find_user_id_by_email(client, base_url, service_role_key, email)
    if not user_id:
        raise LocalDevAuthError(INVALID_CREDENTIALS, 401)

    update_response = await client.put(
        f"{base_url}/auth/v1/admin/users/{user_id}",
        json={"password": password, "email_confirm": True},
        headers=_admin_headers(service_role_key),
        timeout=15.0,
    )
    if update_response.status_code != 200:
        raise LocalDevAuthError(INVALID_CREDENTIALS, 401)


async def _password_grant_session(
    client: httpx.AsyncClient,
    base_url: str,
    anon_key: str,
    email: str,
    password: str,
) -> dict[str, Any]:
    response = await client.post(
        f"{base_url}/auth/v1/token?grant_type=password",
        json={"email": email, "password": password},
        headers={
            "apikey": anon_key,
            "Content-Type": "application/json",
        },
        timeout=15.0,
    )
    if response.status_code != 200:
        raise LocalDevAuthError(INVALID_CREDENTIALS, 401)
    payload = response.json()
    access_token = payload.get("access_token")
    refresh_token = payload.get("refresh_token")
    if not isinstance(access_token, str) or not isinstance(refresh_token, str):
        raise LocalDevAuthError(INVALID_CREDENTIALS, 401)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_in": payload.get("expires_in"),
        "token_type": payload.get("token_type", "bearer"),
    }


async def local_dev_login(email: str, password: str) -> dict[str, Any]:
    settings = get_settings()
    if not local_dev_auth_enabled():
        raise LocalDevAuthError("Not found", 404)

    normalized_email = email.strip().lower()
    allow = normalized_admin_emails(settings)
    if not allow or normalized_email not in allow:
        raise LocalDevAuthError(INVALID_CREDENTIALS, 401)

    expected = settings.local_dev_password
    if not secrets.compare_digest(password, expected):
        raise LocalDevAuthError(INVALID_CREDENTIALS, 401)

    base_url = normalize_supabase_url(settings.supabase_url)
    service_role_key = settings.supabase_service_role_key.strip()
    anon_key = settings.supabase_anon_key.strip()

    async with httpx.AsyncClient() as client:
        await _ensure_auth_user(
            client,
            base_url,
            service_role_key,
            normalized_email,
            expected,
        )
        return await _password_grant_session(
            client,
            base_url,
            anon_key,
            normalized_email,
            expected,
        )
