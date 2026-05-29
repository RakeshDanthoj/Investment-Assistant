from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[1] / "db" / "migrations" / "0022_feed_card_perf.sql"
)


def test_feed_card_perf_migration_defines_expected_indexes() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    for name in (
        "idx_cards_visible_feed_created",
        "idx_cards_lifecycle_created",
        "idx_cards_fog_lifecycle",
        "idx_events_not_synthetic_category",
        "idx_events_major_not_synthetic",
        "idx_instrument_assessments_card_v1",
    ):
        assert name in sql


def test_feed_card_perf_migration_avoids_non_immutable_predicates() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "COALESCE(" not in sql
    assert "lifecycle_state::text" not in sql

