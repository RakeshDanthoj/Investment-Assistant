"""Lens pipeline progress stream (P2-S7)."""

from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.core.auth import CurrentUser
from app.services.cost_guard import MonthlyLLMBudgetError
from app.services.lens_pipeline import run
from app.services.lens_queries import get_query_for_user

router = APIRouter(prefix="/lens", tags=["lens"])


def _sse_payload(data: dict) -> str:
    return f"data: {json.dumps(data, separators=(',', ':'))}\n\n"


@router.get("/queries/{query_id}/stream")
def stream_lens_query(query_id: UUID, current_user: CurrentUser) -> StreamingResponse:
    user_id = UUID(current_user.id)
    row = get_query_for_user(user_id=user_id, query_id=query_id)
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "lens_query_not_found", "message": "Query not found"},
        )

    def event_generator():
        try:
            for payload in run(query_id, user_id=user_id):
                yield _sse_payload(payload)
        except LookupError as exc:
            yield _sse_payload({"event": "error", "message": str(exc)})
        except MonthlyLLMBudgetError as exc:
            yield _sse_payload(
                {"event": "error", "code": "llm_monthly_budget", "message": str(exc)}
            )
        except RuntimeError as exc:
            if "SUPABASE_DB_URL" in str(exc):
                yield _sse_payload(
                    {"event": "error", "message": "Database is temporarily unavailable."}
                )
            else:
                yield _sse_payload({"event": "error", "message": str(exc)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
