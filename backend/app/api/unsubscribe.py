"""One-click email unsubscribe (P2-S10)."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from psycopg.rows import dict_row

from app.db.connection import connection

router = APIRouter(tags=["unsubscribe"])

_SUCCESS_HTML = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Unsubscribed — FinnWise</title>
  </head>
  <body style="font-family:Inter,sans-serif;padding:40px;max-width:480px;margin:0 auto;">
    <h1 style="font-size:20px;">You are unsubscribed</h1>
    <p>Signal-fired emails are turned off for your FinnWise account. You can re-enable them anytime in
    Settings → Email notifications.</p>
  </body>
</html>
"""

_INVALID_HTML = """
<!DOCTYPE html>
<html lang="en">
  <head><meta charset="utf-8" /><title>Link expired — FinnWise</title></head>
  <body style="font-family:Inter,sans-serif;padding:40px;max-width:480px;margin:0 auto;">
    <h1 style="font-size:20px;">This link is invalid or expired</h1>
    <p>If you still receive emails, open FinnWise → Settings → Email notifications to manage preferences.</p>
  </body>
</html>
"""


def apply_unsubscribe_token(token: str) -> bool:
    """
    Consume a single-shot token and disable signal-fired emails.
    Returns True when the token was valid and unused.
    """
    try:
        token_uuid = UUID(token)
    except ValueError:
        return False

    try:
        with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            with conn.transaction():
                cur.execute(
                    """
                    SELECT user_id::text, used_at
                    FROM public.unsubscribe_tokens
                    WHERE token = %s::uuid
                    FOR UPDATE
                    """,
                    (str(token_uuid),),
                )
                row = cur.fetchone()
                if not row or row.get("used_at") is not None:
                    return False

                user_id = str(row["user_id"])
                cur.execute(
                    """
                    UPDATE public.unsubscribe_tokens
                    SET used_at = now()
                    WHERE token = %s::uuid AND used_at IS NULL
                    """,
                    (str(token_uuid),),
                )
                cur.execute(
                    """
                    INSERT INTO public.user_email_preferences (user_id, signal_fired_enabled, updated_at)
                    VALUES (%s::uuid, false, now())
                    ON CONFLICT (user_id) DO UPDATE SET
                      signal_fired_enabled = false,
                      updated_at = now()
                    """,
                    (user_id,),
                )
        return True
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from None


@router.get("/unsubscribe", response_class=HTMLResponse)
def unsubscribe_via_token(token: str = Query(..., min_length=8)) -> HTMLResponse:
    ok = apply_unsubscribe_token(token)
    if not ok:
        return HTMLResponse(content=_INVALID_HTML, status_code=404)
    return HTMLResponse(content=_SUCCESS_HTML)
