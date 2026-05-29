from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[1] / "db" / "migrations" / "0021_synthetic_isolation.sql"
)


def test_synthetic_migration_adds_isolation_columns() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    for col in (
        "is_synthetic",
        "confidence_raw",
        "confidence_effective",
        "is_major",
        "dedup_key",
        "external_id",
    ):
        assert col in sql


def test_synthetic_migration_rls_hides_synthetic_from_authenticated() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "events_hide_synthetic" in sql
    assert "signals_hide_synthetic" in sql
    assert "user_predictions_hide_synthetic" in sql
    assert "card_confidence_history_hide_synthetic" in sql
    assert "NOT is_synthetic" in sql


def test_synthetic_migration_creates_card_confidence_history() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS public.card_confidence_history" in sql
