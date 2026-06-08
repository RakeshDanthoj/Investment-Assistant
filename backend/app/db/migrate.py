from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "db" / "migrations"

MIGRATION_FILES = (
    "0003_enums.sql",
    "0004_core_tables.sql",
    "0005_track_record_append_only.sql",
    "0006_events_dedupe_newsapi_quota.sql",
    "0007_factor_db.sql",
    "0008_cards_llm_budget.sql",
    "0009_editorial_publish_notifications.sql",
    "0010_signal_monitoring.sql",
    "0011_card_bias_flags.sql",
    "0012_user_predictions_unique.sql",
    "0013_tester_acceptances.sql",
    "0014_user_predictions_gap_insight.sql",
    "0015_notifications_card_graded_read_at.sql",
    "0016_lens_queries.sql",
    "0017_user_email_preferences.sql",
    "0018_map_modules.sql",
    "0019_saved_threads.sql",
    "0020_rate_limit_observability.sql",
    "0021_synthetic_isolation.sql",
    "0022_feed_card_perf.sql",
    "0023_dedup_key_review_queue.sql",
    "0024_factor_poll_log.sql",
    "0025_watchlist_items.sql",
    "0026_pipeline_runs_held_status.sql",
    "0027_confidence_audit.sql",
    "0028_card_regen_history.sql",
    "0029_performance_read_views.sql",
)

_SCHEMA_MIGRATIONS_DDL = """
CREATE TABLE IF NOT EXISTS public.schema_migrations (
  filename text PRIMARY KEY,
  applied_at timestamptz NOT NULL DEFAULT now()
);
"""


def _applied_migrations(cursor) -> set[str]:
    cursor.execute("SELECT filename FROM public.schema_migrations")
    return {row[0] for row in cursor.fetchall()}


def apply_migrations(connection) -> None:
    """Run P1-S4 SQL migrations in order; skip files already recorded."""
    with connection.cursor() as cursor:
        cursor.execute(_SCHEMA_MIGRATIONS_DDL)
        applied = _applied_migrations(cursor)

        for filename in MIGRATION_FILES:
            if filename in applied:
                continue
            sql = (MIGRATIONS_DIR / filename).read_text(encoding="utf-8")
            with connection.transaction():
                cursor.execute(sql)
                cursor.execute(
                    "INSERT INTO public.schema_migrations (filename) VALUES (%s)",
                    (filename,),
                )
