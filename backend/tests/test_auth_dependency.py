from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.core.auth import User, get_current_user, verify_supabase_token


@pytest.mark.asyncio
async def test_verify_supabase_token_valid() -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "user-123",
        "email": "tester@finnwise.test",
        "role": "authenticated",
        "user_metadata": {"full_name": "Test User"},
    }

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.core.auth.httpx.AsyncClient", return_value=mock_client):
        user = await verify_supabase_token("valid-token")

    assert user == User(
        id="user-123",
        email="tester@finnwise.test",
        role="authenticated",
        user_metadata={"full_name": "Test User"},
    )


@pytest.mark.asyncio
async def test_verify_supabase_token_invalid() -> None:
    mock_response = MagicMock()
    mock_response.status_code = 401

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.core.auth.httpx.AsyncClient", return_value=mock_client):
        with pytest.raises(HTTPException) as exc_info:
            await verify_supabase_token("invalid-token")

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_missing_header() -> None:
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(None)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_invalid_token() -> None:
    with patch(
        "app.core.auth.verify_supabase_token",
        side_effect=HTTPException(status_code=401, detail="Invalid or expired token"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user("Bearer bad-token")

    assert exc_info.value.status_code == 401
