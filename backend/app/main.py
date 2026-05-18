from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.admin_queue import router as admin_router
from app.api.admin_review import router as admin_review_router
from app.api.admin_signal_queue import router as admin_signal_queue_router
from app.api.cards import router as cards_router
from app.api.cards_detail import router as cards_detail_router
from app.api.factor_db import router as factor_db_router
from app.api.feed import router as feed_router
from app.api.notifications import router as notifications_router
from app.api.predictions import router as predictions_router
from app.api.onboarding import router as onboarding_router
from app.core.settings import get_settings

app = FastAPI(title="FinnWise API", version="0.1.0")

settings = get_settings()

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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
