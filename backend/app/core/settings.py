from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, field_validator
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

    @field_validator("supabase_url", mode="before")
    @classmethod
    def _normalize_supabase_url(cls, v: object) -> object:
        if isinstance(v, str):
            return normalize_supabase_url(v)
        return v
    supabase_db_url: str = ""
    gemini_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    )
    gemini_model: str = Field(default="gemini-2.0-flash", validation_alias="GEMINI_MODEL")

    @field_validator("gemini_model", mode="before")
    @classmethod
    def _gemini_model_fallback(cls, v: object) -> object:
        if v is None:
            return "gemini-2.0-flash"
        if isinstance(v, str) and not v.strip():
            return "gemini-2.0-flash"
        return v
    newsapi_key: str = ""
    factor_db_admin_emails: str = ""
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,https://*.vercel.app"


@lru_cache
def get_settings() -> Settings:
    return Settings()
