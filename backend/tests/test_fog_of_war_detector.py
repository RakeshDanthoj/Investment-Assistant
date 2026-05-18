"""Fog of War detection rules (P1-S9)."""

from app.services.feed import (
    FOG_LIFECYCLE,
    detect_fog_of_war,
    horizon_cutoff,
    tier_label,
)


def test_detect_fog_requires_three_relevant_cards() -> None:
    rows = [
        ("active", "macro"),
        ("active", "macro"),
    ]
    assert detect_fog_of_war(major_active_cards=rows) is False


def test_detect_fog_false_when_categories_are_all_distinct() -> None:
    rows = [
        ("active", "macro"),
        ("active", "rbi_policy"),
        ("signal_triggered", "regulatory"),
    ]
    assert detect_fog_of_war(major_active_cards=rows) is False


def test_detect_fog_true_when_three_plus_and_category_overlap() -> None:
    rows = [
        ("active", "macro"),
        ("signal_triggered", "macro"),
        ("active", "rbi_policy"),
    ]
    assert detect_fog_of_war(major_active_cards=rows) is True


def test_detect_fog_ignores_non_fog_lifecycle() -> None:
    rows = [
        ("published", "macro"),
        ("published", "macro"),
        ("published", "macro"),
    ]
    assert detect_fog_of_war(major_active_cards=rows) is False


def test_fog_lifecycle_set_contains_expected() -> None:
    assert FOG_LIFECYCLE == {"active", "signal_triggered"}


def test_horizon_cutoff_under_one_year() -> None:
    from datetime import UTC, datetime

    now = datetime(2026, 1, 1, tzinfo=UTC)
    c = horizon_cutoff("under_1y", now=now)
    assert c is not None
    assert (now - c).days == 365


def test_horizon_cutoff_seven_plus_is_none() -> None:
    assert horizon_cutoff("7_plus") is None


def test_tier_label_covers_tiers() -> None:
    assert tier_label("high") == "High"
    assert tier_label("moderate") == "Moderate"
    assert tier_label("uncertain") == "Uncertain"
