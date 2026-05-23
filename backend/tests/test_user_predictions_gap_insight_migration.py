"""Migration 0014 adds gap_insight to user_predictions (P2-S2)."""

from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "db"
    / "migrations"
    / "0014_user_predictions_gap_insight.sql"
)


def test_migration_adds_gap_insight_column() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "gap_insight" in sql
    assert "user_predictions" in sql
