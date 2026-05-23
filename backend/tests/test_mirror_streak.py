"""Mirror streak grid ordering and summary (P2-S5)."""

from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.mirror_streak import router as mirror_streak_router
from app.core.auth import User, get_current_user
from app.services.mirror_streak import (
    STREAK_SLOT_COUNT,
    MirrorStreakResult,
    StreakCell,
    build_streak_cells,
    build_streak_summary,
    cell_from_mechanism_grade,
)

app = FastAPI()
app.include_router(mirror_streak_router, prefix="/api")
client = TestClient(app)

TEST_USER = User(id=str(uuid4()), email="streak@finnwise.test")


@pytest.fixture(autouse=True)
def override_auth():
    async def _user():
        return TEST_USER

    app.dependency_overrides[get_current_user] = _user
    yield
    app.dependency_overrides.clear()


def test_cell_from_mechanism_grade_letters() -> None:
    assert cell_from_mechanism_grade("correct").letter == "M"
    assert cell_from_mechanism_grade("partial").letter == "P"
    assert cell_from_mechanism_grade("incorrect").letter == "✗"
    assert cell_from_mechanism_grade("monitoring").letter == "·"
    assert cell_from_mechanism_grade(None).letter == "·"


def test_build_streak_cells_most_recent_first_with_transparent_padding() -> None:
    grades = ["correct", "partial", "incorrect", None]
    cells = build_streak_cells(grades)

    assert len(cells) == STREAK_SLOT_COUNT
    assert cells[0].grade == "correct"
    assert cells[1].grade == "partial"
    assert cells[2].grade == "incorrect"
    assert cells[3].grade == "monitoring"
    assert all(c.grade == "empty" and c.letter == "–" for c in cells[4:])


def test_build_streak_summary_includes_both_percentages_when_gap_is_wide() -> None:
    text = build_streak_summary(80.0, 45.0)
    assert "80%" in text
    assert "45%" in text
    assert "normal" in text.lower()


def test_mirror_streak_route_returns_fourteen_cells(monkeypatch) -> None:
    cells = [StreakCell("M", "correct")] + [
        StreakCell("–", "empty") for _ in range(STREAK_SLOT_COUNT - 1)
    ]
    result = MirrorStreakResult(
        cells=cells,
        mechanism_accuracy_pct=100.0,
        market_accuracy_pct=50.0,
        summary="Test summary",
    )
    monkeypatch.setattr("app.api.mirror_streak.streak_for_user", lambda _uid: result)

    res = client.get("/api/mirror/streak")
    assert res.status_code == 200
    payload = res.json()
    assert len(payload["cells"]) == STREAK_SLOT_COUNT
    assert payload["cells"][0]["letter"] == "M"
    assert payload["cells"][1]["grade"] == "empty"
    assert payload["mechanism_accuracy_pct"] == 100.0
    assert payload["market_accuracy_pct"] == 50.0
    assert payload["summary"] == "Test summary"
