from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[1] / "db" / "migrations" / "0029_performance_read_views.sql"
)


def test_performance_views_migration_defines_expected_views() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    for name in (
        "map_sector_list_v",
        "map_sector_summary_v",
        "map_sector_matrix_v",
        "mirror_user_predictions_v",
        "mirror_user_streak_v",
        "mirror_graded_history_v",
        "lens_user_queries_v",
    ):
        assert f"public.{name}" in sql


def test_performance_views_migration_excludes_synthetic_mirror_rows() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "up.is_synthetic IS NOT TRUE" in sql
    assert "e.is_synthetic IS NOT TRUE" in sql


def test_performance_views_migration_caps_ranked_history() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "streak_rank <= 14" in sql
    assert "history_rank <= 50" in sql


def test_performance_views_migration_uses_json_for_map_payloads() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "json_build_object" in sql
    assert "json_agg" in sql
    assert "sensitivity_rows" in sql
