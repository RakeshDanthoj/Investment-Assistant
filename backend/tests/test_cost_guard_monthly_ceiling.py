"""Monthly LLM INR budget guard (P2-S13)."""

from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.lens import router as lens_router
from app.core.auth import User, get_current_user
from app.core.settings import get_settings
from app.services.cost_guard import MonthlyLLMBudgetError, check_monthly_budget_or_raise

app = FastAPI()
app.include_router(lens_router, prefix="/api")
client = TestClient(app)

TEST_USER = User(id=str(uuid4()), email="budget@finnwise.test")


@pytest.fixture(autouse=True)
def override_auth():
    async def _user():
        return TEST_USER

    app.dependency_overrides[get_current_user] = _user
    yield
    app.dependency_overrides.clear()


def test_check_monthly_budget_or_raise_aborts_when_projected_over(monkeypatch):
    monkeypatch.setenv("LLM_MONTHLY_BUDGET_INR", "100")
    monkeypatch.setenv("USD_INR_RATE", "100")
    get_settings.cache_clear()

    monkeypatch.setattr(
        "app.services.cost_guard.month_to_date_spend_usd",
        lambda: 0.99,
    )

    with pytest.raises(MonthlyLLMBudgetError, match="monthly LLM budget exceeded"):
        check_monthly_budget_or_raise(additional_usd=0.02)


def test_check_monthly_budget_skipped_when_budget_zero(monkeypatch):
    monkeypatch.setenv("LLM_MONTHLY_BUDGET_INR", "0")
    get_settings.cache_clear()
    monkeypatch.setattr(
        "app.services.cost_guard.month_to_date_spend_usd",
        lambda: 9999.0,
    )
    check_monthly_budget_or_raise()


def test_post_lens_query_returns_monthly_budget_error(monkeypatch):
    monkeypatch.setattr("app.api.lens.enforce_lens_daily_limit", lambda **_: None)

    def _raise_budget(**_kwargs):
        raise MonthlyLLMBudgetError("monthly LLM budget exceeded: projected ₹25000 > ceiling ₹20000")

    monkeypatch.setattr("app.api.lens.check_monthly_budget_or_raise", _raise_budget)

    res = client.post(
        "/api/lens/queries",
        json={"query": "What would a US recession mean for Indian IT exporters?"},
    )
    assert res.status_code == 402
    assert res.json()["detail"]["code"] == "llm_monthly_budget"
