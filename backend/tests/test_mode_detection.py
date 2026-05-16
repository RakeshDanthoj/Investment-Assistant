"""Nine-case grid: three postures × three horizon buckets (see mode_detection._BUCKET)."""

import pytest

from app.services.mode_detection import (
    Horizon,
    InvestmentStatus,
    detect_mode,
    horizon_bucket,
)


@pytest.mark.parametrize(
    ("status", "horizon", "expected_mode", "expected_surface"),
    [
        # curious × three buckets
        ("curious", "under_1y", "curious", "pulse"),
        ("curious", "3_7y", "curious", "pulse"),
        ("curious", "7_plus", "curious", "pulse"),
        # starting_fresh × three buckets → Portfolio Builder → Map
        ("starting_fresh", "under_1y", "portfolio_builder", "map"),
        ("starting_fresh", "3_7y", "portfolio_builder", "map"),
        ("starting_fresh", "7_plus", "portfolio_builder", "map"),
        # has_investments × three buckets → Protector → Pulse
        ("has_investments", "under_1y", "portfolio_protector", "pulse"),
        ("has_investments", "3_7y", "portfolio_protector", "pulse"),
        ("has_investments", "7_plus", "portfolio_protector", "pulse"),
    ],
)
def test_detect_mode_nine_case_grid(
    status: InvestmentStatus,
    horizon: Horizon,
    expected_mode: str,
    expected_surface: str,
) -> None:
    mode, surface, rationale = detect_mode(status, horizon)
    assert mode == expected_mode
    assert surface == expected_surface
    assert rationale


def test_horizon_bucket_groups_four_horizons_into_three_buckets() -> None:
    assert horizon_bucket("under_1y") == horizon_bucket("1_3y") == "short"
    assert horizon_bucket("3_7y") == "mid"
    assert horizon_bucket("7_plus") == "long"


def test_detect_mode_rationale_differs_by_bucket_for_same_status() -> None:
    _, _, r_short = detect_mode("has_investments", "under_1y")
    _, _, r_long = detect_mode("has_investments", "7_plus")
    assert r_short != r_long
