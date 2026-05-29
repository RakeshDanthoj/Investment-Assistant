from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[1] / "db" / "migrations" / "0024_factor_poll_log.sql"
)


def test_factor_poll_log_migration_schema() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS public.factor_poll_log" in sql
    assert "factor_id uuid NOT NULL REFERENCES public.factors" in sql
    assert "status text NOT NULL CHECK (status IN ('ok', 'empty', 'error'))" in sql
    assert "article_count smallint" in sql
