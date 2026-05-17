from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[3]
_ENV_FILE = _REPO_ROOT / ".env.local"


def normalize_supabase_url(url: str) -> str:
    if not url:
        return ""
    if url.startswith("http"):
        return url.rstrip("/")
    return f"https://{url}.supabase.co"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_db_url: str = ""
    claude_api_key: str = ""
    newsapi_key: str = ""
    factor_db_admin_emails: str = ""
    cors_origins: str = "http://localhost:3000,https://*.vercel.app"


@lru_cache
def get_settings() -> Settings:
    return Settings()
