from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[1] / "db" / "migrations" / "0023_dedup_key_review_queue.sql"
)


def test_dedup_migration_adds_merge_columns() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    for col in ("source_count", "sources", "force_editorial_review", "collision_fingerprint"):
        assert col in sql


def test_dedup_migration_creates_review_queue() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS public.dedup_review_queue" in sql
    assert "event_ids uuid[]" in sql
    assert "status text" in sql


def test_dedup_migration_source_count_guardrail_comment() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "source_count > 5" in sql
