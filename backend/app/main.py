from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from psycopg import Error as PsycopgError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.api.admin_queue import router as admin_router
from app.api.admin_review import router as admin_review_router
from app.api.admin_signal_queue import router as admin_signal_queue_router
from app.api.cards import router as cards_router
from app.api.cards_detail import router as cards_detail_router
from app.api.factor_db import router as factor_db_router
from app.api.feed import router as feed_router
from app.api.notifications import router as notifications_router
from app.api.onboarding import router as onboarding_router
from app.api.predictions import router as predictions_router
from app.api.tester_acceptance import router as tester_acceptance_router
from app.core.settings import get_settings
from app.db.connection import close_db_pool, connection, init_db_pool
from app.diagnostics.timing import DbRequestTimer
from app.http.cache_control import NO_STORE_CACHE


class AdminNoStoreCacheMiddleware(BaseHTTPMiddleware):
    """Editorial/admin paths must never be cached (P1.5-S4)."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        path = request.url.path
        if path.startswith("/api/admin") or path.startswith("/admin"):
            response.headers["Cache-Control"] = NO_STORE_CACHE
        return response


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db_pool()
    yield
    close_db_pool()


app = FastAPI(title="FinnWise API", version="0.1.0", lifespan=lifespan)


@app.exception_handler(PsycopgError)
async def psycopg_error_handler(_request: Request, exc: PsycopgError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "detail": {
                "code": "db_unavailable",
                "message": f"Database query failed: {exc}",
            }
        },
    )


settings = get_settings()

app.add_middleware(AdminNoStoreCacheMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_origin_regex=r"https://[\w-]+\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(onboarding_router, prefix="/onboarding", tags=["onboarding"])
app.include_router(admin_router, prefix="/admin")
app.include_router(admin_review_router, prefix="/api/admin")
app.include_router(admin_signal_queue_router, prefix="/api/admin")
app.include_router(factor_db_router, prefix="/api", tags=["factor-db"])
app.include_router(feed_router, prefix="/api", tags=["feed"])
app.include_router(cards_router, prefix="/api/cards", tags=["cards"])
app.include_router(notifications_router, prefix="/api", tags=["notifications"])
app.include_router(cards_detail_router, prefix="/api/cards", tags=["cards"])
app.include_router(predictions_router, prefix="/api", tags=["predictions"])
app.include_router(tester_acceptance_router, prefix="/api", tags=["tester"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db")
def health_db() -> dict[str, object]:
    """Check direct Postgres connectivity (Pulse, Thread, Factor DB)."""
    db_url = get_settings().supabase_db_url.strip()
    if not db_url:
        return {
            "status": "error",
            "code": "db_unconfigured",
            "message": "SUPABASE_DB_URL is not set on this service.",
        }
    try:
        with DbRequestTimer() as timer, connection() as conn, conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM public.cards")
            card_count = int(cur.fetchone()[0])
        timing = timer.snapshot()
        return {
            "status": "ok",
            "cards": card_count,
            "connect_ms": timing["db_connect_ms"],
            "query_ms": timing["db_query_ms"],
            "total_ms": timing["total_ms"],
        }
    except RuntimeError as exc:
        return {"status": "error", "code": "db_unavailable", "message": str(exc)}
    except PsycopgError as exc:
        return {"status": "error", "code": "db_unavailable", "message": str(exc)}
