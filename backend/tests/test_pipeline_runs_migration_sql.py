from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "db"
    / "migrations"
    / "0026_pipeline_runs_held_status.sql"
)


def test_pipeline_runs_migration_allows_held_status() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "pipeline_runs_status_check" in sql
    assert "'held'" in sql
