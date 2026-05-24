"""P2-S4 — reasoning gap detector heuristics and API."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.auth import User, get_current_user
from app.db.migrate import apply_migrations
from app.db.seeds import apply_all_factor_db_seeds
from app.main import app
from app.services.reasoning_gap_detector import (
    MIN_GRADED_RESOLVED,
    GradedPredictionRow,
    analyse_from_history,
    infer_gap_type_for_prediction,
    score_gap_types,
)
from app.services.reasoning_gap_map import GAP_TYPE_LABELS

TEST_USER = User(id=str(uuid4()), email="gaps@finnwise.test")


def _row(
    *,
    mech: str | None = "correct",
    biz: str | None = "partial",
    market: str | None = "incorrect",
    sector: str | None = "banking",
) -> GradedPredictionRow:
    return GradedPredictionRow(
        mechanism_accuracy=mech,
        business_accuracy=biz,
        market_accuracy=market,
        sector_slug=sector,
    )


def test_insufficient_history_returns_empty() -> None:
    history = [_row(), _row()]
    assert len(history) < MIN_GRADED_RESOLVED
    assert analyse_from_history(history) == []


def test_direction_magnitude_pattern_surfaces() -> None:
    history = [
        _row(mech="correct", market="incorrect", sector="banking"),
        _row(mech="correct", market="partial", sector="it"),
        _row(mech="correct", market="incorrect", sector="energy"),
        _row(mech="incorrect", market="incorrect", sector="fmcg"),
    ]
    scored = score_gap_types(history)
    assert scored
    assert scored[0].gap_type == "direction_magnitude_mismatch"
    assert "mechanism was correct" in scored[0].pattern_explanation


def test_narrative_anchoring_pattern_surfaces() -> None:
    history = [
        _row(mech="incorrect", biz="correct", market="partial"),
        _row(mech="partial", biz="correct", market="incorrect"),
        _row(mech="incorrect", biz="correct", market="partial"),
        _row(mech="correct", biz="correct", market="correct"),
    ]
    scored = score_gap_types(history)
    types = {s.gap_type for s in scored}
    assert "narrative_anchoring" in types


def test_sector_concentration_pattern_surfaces() -> None:
    history = [
        _row(sector="banking"),
        _row(sector="banking"),
        _row(sector="banking"),
        _row(sector="it"),
    ]
    scored = score_gap_types(history)
    types = {s.gap_type for s in scored}
    assert "sector_concentration" in types


def test_infer_per_prediction_gap_type() -> None:
    assert (
        infer_gap_type_for_prediction("correct", "partial", "incorrect")
        == "direction_magnitude_mismatch"
    )
    assert (
        infer_gap_type_for_prediction("incorrect", "correct", "partial")
        == "narrative_anchoring"
    )
    assert infer_gap_type_for_prediction("correct", "correct", "correct") is None


@pytest.fixture(scope="module")
def gaps_client(db_connection):
    apply_migrations(db_connection)
    apply_all_factor_db_seeds(db_connection)
    db_connection.commit()
    return TestClient(app)


@pytest.fixture(autouse=True)
def override_auth():
    async def _user():
        return TEST_USER

    app.dependency_overrides[get_current_user] = _user
    yield
    app.dependency_overrides.clear()


def test_mirror_gaps_api_insufficient_history(gaps_client) -> None:
    res = gaps_client.get("/api/mirror/gaps", headers={"Authorization": "Bearer t"})
    assert res.status_code == 200
    body = res.json()
    assert body["insufficient_history"] is True
    assert body["items"] == []


def test_mirror_gaps_refresh_endpoint(gaps_client) -> None:
    res = gaps_client.post(
        "/api/mirror/gaps/refresh",
        headers={"Authorization": "Bearer t"},
    )
    assert res.status_code == 200
    assert "items" in res.json()


def test_analyse_from_history_links_map_module_names(gaps_client) -> None:
    del gaps_client
    history = [
        _row(mech="correct", market="incorrect"),
        _row(mech="correct", market="partial"),
        _row(mech="correct", market="incorrect"),
    ]
    gaps = analyse_from_history(history)
    assert len(gaps) >= 1
    gap = gaps[0]
    assert gap.gap_name == GAP_TYPE_LABELS[gap.gap_type]
    assert gap.linked_map_module_id
    assert gap.linked_map_module_name
