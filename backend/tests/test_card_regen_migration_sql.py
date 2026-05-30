from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "db"
    / "migrations"
    / "0028_card_regen_history.sql"
)


def test_card_regen_migration_adds_audit_columns() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "regen_history" in sql
    assert "full_regen_count" in sql
    assert "po_regen_flag_cleared" in sql
