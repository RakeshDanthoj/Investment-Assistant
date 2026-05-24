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
    supabase_db_url: str = ""
    gemini_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("GEMINI_API_KEY", "GOOGLE_API_KEY"),
    )
    gemini_model: str = Field(default="gemini-2.0-flash", validation_alias="GEMINI_MODEL")

    @field_validator("supabase_url", mode="before")
    @classmethod
    def _normalize_supabase_url(cls, v: object) -> object:
        if isinstance(v, str):
            return normalize_supabase_url(v)
        return v

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
    admin_emails: str = Field(default="", validation_alias="ADMIN_EMAILS")
    llm_monthly_budget_inr: float = Field(
        default=20_000.0,
        validation_alias="LLM_MONTHLY_BUDGET_INR",
    )
    usd_inr_rate: float = Field(default=85.0, validation_alias="USD_INR_RATE")
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000,https://*.vercel.app"
    personalisation_token_salt: str = Field(
        default="dev-personalisation-salt-change-me",
        validation_alias="PERSONALISATION_TOKEN_SALT",
    )

    email_provider: str = Field(default="", validation_alias="EMAIL_PROVIDER")
    email_api_key: str = Field(default="", validation_alias="EMAIL_API_KEY")
    email_from: str = Field(default="", validation_alias="EMAIL_FROM")
    app_public_url: str = Field(default="", validation_alias="APP_PUBLIC_URL")

    signal_facts_events_enabled: bool = Field(
        default=True,
        validation_alias="SIGNAL_FACTS_EVENTS_ENABLED",
    )
    signal_facts_nse_enabled: bool = Field(
        default=True,
        validation_alias="SIGNAL_FACTS_NSE_ENABLED",
    )
    signal_facts_index_enabled: bool = Field(
        default=True,
        validation_alias="SIGNAL_FACTS_INDEX_ENABLED",
    )
    signal_facts_max_total: int = Field(
        default=300,
        validation_alias="SIGNAL_FACTS_MAX_TOTAL",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
