"""Migration 0015 adds lens_queries (P2-S6)."""

from pathlib import Path

MIGRATION = Path(__file__).resolve().parents[1] / "db" / "migrations" / "0016_lens_queries.sql"


def test_migration_defines_lens_queries_table() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "lens_queries" in sql
    assert "lens_query_status" in sql
    assert "'queued'" in sql
    assert "'running'" in sql
    assert "'done'" in sql
    assert "'failed'" in sql
