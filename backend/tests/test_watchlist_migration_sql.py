from pathlib import Path

MIGRATION = Path(__file__).resolve().parents[1] / "db" / "migrations" / "0025_watchlist_items.sql"


def test_watchlist_migration_creates_table() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS public.watchlist_items" in sql
    assert "status IN ('watching', 'escalated', 'closed')" in sql


def test_watchlist_migration_seeds_five_rows() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert sql.count("a1000001-0001-4001-8001-") == 5
    assert "ON CONFLICT (id) DO NOTHING" in sql
