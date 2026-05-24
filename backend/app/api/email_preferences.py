"""Authenticated email preference routes (P2-S10)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from psycopg.rows import dict_row
from pydantic import BaseModel, Field

from app.core.auth import CurrentUser
from app.db.connection import connection

router = APIRouter(prefix="/email", tags=["email"])


class EmailPreferencesResponse(BaseModel):
    signal_fired_enabled: bool


class EmailPreferencesUpdate(BaseModel):
    signal_fired_enabled: bool = Field(..., description="Receive emails when a watched signal fires")


def get_preferences(cur, user_id: str) -> bool:
    cur.execute(
        """
        INSERT INTO public.user_email_preferences (user_id, signal_fired_enabled)
        VALUES (%s::uuid, true)
        ON CONFLICT (user_id) DO NOTHING
        """,
        (user_id,),
    )
    cur.execute(
        """
        SELECT signal_fired_enabled
        FROM public.user_email_preferences
        WHERE user_id = %s::uuid
        """,
        (user_id,),
    )
    row = cur.fetchone()
    if not row:
        return True
    return bool(row["signal_fired_enabled"] if isinstance(row, dict) else row[0])


def set_preferences(cur, user_id: str, *, signal_fired_enabled: bool) -> None:
    cur.execute(
        """
        INSERT INTO public.user_email_preferences (user_id, signal_fired_enabled, updated_at)
        VALUES (%s::uuid, %s, now())
        ON CONFLICT (user_id) DO UPDATE SET
          signal_fired_enabled = EXCLUDED.signal_fired_enabled,
          updated_at = now()
        """,
        (user_id, signal_fired_enabled),
    )


@router.get("/preferences", response_model=EmailPreferencesResponse)
def read_email_preferences(current_user: CurrentUser) -> EmailPreferencesResponse:
    try:
        with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            enabled = get_preferences(cur, current_user.id)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return EmailPreferencesResponse(signal_fired_enabled=enabled)


@router.put("/preferences", response_model=EmailPreferencesResponse)
def update_email_preferences(
    body: EmailPreferencesUpdate,
    current_user: CurrentUser,
) -> EmailPreferencesResponse:
    try:
        with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            with conn.transaction():
                set_preferences(
                    cur,
                    current_user.id,
                    signal_fired_enabled=body.signal_fired_enabled,
                )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    return EmailPreferencesResponse(signal_fired_enabled=body.signal_fired_enabled)
