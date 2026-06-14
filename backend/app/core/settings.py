from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
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
    nvidia_api_key: str = Field(default="", validation_alias="NVIDIA_API_KEY")
    llm_model: str = Field(
        default="nvidia/nemotron-3-super-120b-a12b",
        validation_alias="LLM_MODEL",
    )
    llm_base_url: str = Field(
        default="https://integrate.api.nvidia.com/v1",
        validation_alias="LLM_BASE_URL",
    )
    llm_request_timeout_seconds: float = Field(
        default=90.0,
        validation_alias="LLM_REQUEST_TIMEOUT_SECONDS",
    )
    llm_max_retries: int = Field(
        default=2,
        validation_alias="LLM_MAX_RETRIES",
    )
    draft_pipeline_max_llm_calls: int = Field(
        default=5,
        validation_alias="DRAFT_PIPELINE_MAX_LLM_CALLS",
    )

    def draft_pipeline_deadline_seconds(self) -> float:
        """
        Wall-clock budget for draft-from-event (synthesis×2 + dissent + framework).

        Each slot allows up to llm_max_retries per-call attempts at llm_request_timeout_seconds.
        """
        return (
            float(self.llm_request_timeout_seconds)
            * max(1, int(self.llm_max_retries))
            * max(1, int(self.draft_pipeline_max_llm_calls))
        )

    @field_validator("supabase_url", mode="before")
    @classmethod
    def _normalize_supabase_url(cls, v: object) -> object:
        if isinstance(v, str):
            return normalize_supabase_url(v)
        return v

    @field_validator("llm_model", mode="before")
    @classmethod
    def _llm_model_fallback(cls, v: object) -> object:
        if v is None:
            return "nvidia/nemotron-3-super-120b-a12b"
        if isinstance(v, str) and not v.strip():
            return "nvidia/nemotron-3-super-120b-a12b"
        return v

    @field_validator("llm_base_url", mode="before")
    @classmethod
    def _llm_base_url_fallback(cls, v: object) -> object:
        if v is None:
            return "https://integrate.api.nvidia.com/v1"
        if isinstance(v, str) and not v.strip():
            return "https://integrate.api.nvidia.com/v1"
        return v

    newsapi_key: str = ""
    factor_db_admin_emails: str = ""
    admin_emails: str = Field(default="", validation_alias="ADMIN_EMAILS")
    local_dev_password: str = Field(default="", validation_alias="LOCAL_DEV_PASSWORD")
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
    open_exchange_rates_app_id: str = Field(
        default="",
        validation_alias="OPEN_EXCHANGE_RATES_APP_ID",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
