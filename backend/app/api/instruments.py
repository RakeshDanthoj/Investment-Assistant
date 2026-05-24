"""Instrument search for session holdings entry (P2-S9)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.diagnostics.timing import DbRequestTimer, json_response_with_timing
from app.http.cache_control import NO_STORE_CACHE
from app.services.instruments_search import search_instruments

router = APIRouter()


@router.get("/instruments/search")
def get_instrument_search(
    q: str = Query(..., min_length=1, max_length=64, description="Ticker or name prefix"),
) -> JSONResponse:
    with DbRequestTimer() as timer:
        try:
            rows = search_instruments(q, limit=10)
        except RuntimeError as exc:
            if "SUPABASE_DB_URL" in str(exc):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail={"code": "db_unavailable", "message": str(exc)},
                ) from exc
            raise
    return json_response_with_timing(
        {"results": rows},
        timer,
        cache_control=NO_STORE_CACHE,
    )
