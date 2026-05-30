from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[1] / "db" / "migrations" / "0027_confidence_audit.sql"
)


def test_confidence_audit_migration_schema() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS public.confidence_score_audit" in sql
    assert "event_id uuid NOT NULL REFERENCES public.events" in sql
    assert "inputs_json jsonb NOT NULL" in sql
    assert "scorer_version text NOT NULL" in sql
    assert "factor_db_match_count smallint" in sql
