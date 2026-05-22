"""Tester acceptance gate — blocks API use until briefing accepted (P1-S14)."""

from datetime import UTC
from uuid import uuid4

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.tester_acceptance import require_tester_acceptance
from app.api.tester_acceptance import router as acceptance_router
from app.core.auth import User, get_current_user

app = FastAPI()
app.include_router(acceptance_router, prefix="/api")


@app.get("/api/protected/feature")
def protected_feature(
    _: None = Depends(require_tester_acceptance),
    user: User = Depends(get_current_user),
):
    return {"ok": True, "user_id": user.id}


client = TestClient(app)
TEST_USER = User(id=str(uuid4()), email="tester@finnwise.test")


@pytest.fixture(autouse=True)
def override_auth():
    async def _user():
        return TEST_USER

    app.dependency_overrides[get_current_user] = _user
    yield
    app.dependency_overrides.clear()


def test_post_tester_accept_requires_auth():
    app.dependency_overrides.clear()
    res = client.post("/api/tester/accept")
    assert res.status_code == 401


def test_post_tester_accept_records_row(monkeypatch):
    seen: dict = {}

    def _record(*, user_id: str, ip: str | None):
        seen["user_id"] = user_id
        seen["ip"] = ip
        from datetime import datetime

        return datetime.now(UTC)

    monkeypatch.setattr("app.api.tester_acceptance.has_accepted", lambda _uid: False)
    monkeypatch.setattr("app.api.tester_acceptance.record_acceptance", _record)

    res = client.post("/api/tester/accept")
    assert res.status_code == 200
    assert res.json()["ok"] is True
    assert seen["user_id"] == TEST_USER.id


def test_require_tester_acceptance_blocks_when_not_accepted(monkeypatch):
    monkeypatch.setattr("app.api.tester_acceptance.has_accepted", lambda _uid: False)

    res = client.get("/api/protected/feature")
    assert res.status_code == 403
    detail = res.json()["detail"]
    assert detail["code"] == "tester_acceptance_required"


def test_require_tester_acceptance_allows_when_accepted(monkeypatch):
    monkeypatch.setattr("app.api.tester_acceptance.has_accepted", lambda _uid: True)

    res = client.get("/api/protected/feature")
    assert res.status_code == 200
    assert res.json()["user_id"] == TEST_USER.id


def test_get_tester_status_reflects_acceptance(monkeypatch):
    monkeypatch.setattr("app.api.tester_acceptance.has_accepted", lambda _uid: True)
    res = client.get("/api/tester/status")
    assert res.status_code == 200
    assert res.json()["accepted"] is True

    monkeypatch.setattr("app.api.tester_acceptance.has_accepted", lambda _uid: False)
    res = client.get("/api/tester/status")
    assert res.json()["accepted"] is False
