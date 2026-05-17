from pathlib import Path

MIGRATION = Path(__file__).resolve().parents[1] / "db" / "migrations" / "0007_factor_db.sql"


def test_factor_db_migration_requires_mmj_and_source_url() -> None:
    sql = MIGRATION.read_text(encoding="utf-8").lower()
    lowered = sql.replace("\n", " ")
    assert "instrument_factor_sensitivity" in sql
    assert "public.mmj_type not null" in lowered
    assert "create table if not exists public.factors" in sql
    assert "create table if not exists public.instruments" in sql
    assert "source_url" in sql
