from datetime import UTC, datetime, timedelta

from app.services.factor_db import freshness_for_retrieved_at

GREEN_MAX_DAYS = round(365.25 * 0.5)  # mirrors service (≈183)
AMBER_MAX_DAYS = round(365.25 * 1.5)  # (≈548)


def test_freshness_green_at_green_upper_bound() -> None:
    ref = datetime(2026, 5, 17, 12, tzinfo=UTC)
    retrieved = ref - timedelta(days=GREEN_MAX_DAYS)
    assert freshness_for_retrieved_at(retrieved, reference=ref) == "green"


def test_freshness_amber_just_over_green() -> None:
    ref = datetime(2026, 5, 17, 12, tzinfo=UTC)
    retrieved = ref - timedelta(days=GREEN_MAX_DAYS + 1)
    assert freshness_for_retrieved_at(retrieved, reference=ref) == "amber"


def test_freshness_amber_at_upper_bound() -> None:
    ref = datetime(2026, 5, 17, 12, tzinfo=UTC)
    retrieved = ref - timedelta(days=AMBER_MAX_DAYS)
    assert freshness_for_retrieved_at(retrieved, reference=ref) == "amber"


def test_freshness_red_beyond_amber() -> None:
    ref = datetime(2026, 5, 17, 12, tzinfo=UTC)
    retrieved = ref - timedelta(days=AMBER_MAX_DAYS + 1)
    assert freshness_for_retrieved_at(retrieved, reference=ref) == "red"
