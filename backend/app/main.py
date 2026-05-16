from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
