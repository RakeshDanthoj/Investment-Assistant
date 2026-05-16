from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[1] / "db" / "migrations" / "0005_track_record_append_only.sql"
)


def test_track_record_migration_revokes_update_and_delete() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "REVOKE UPDATE, DELETE ON public.track_record" in sql
    assert "FROM service_role" in sql


def test_track_record_migration_defines_deny_triggers() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "track_record_deny_update" in sql
    assert "track_record_deny_delete" in sql
    assert "deny_track_record_mutation" in sql
