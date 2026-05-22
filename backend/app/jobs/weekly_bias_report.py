"""Weekly editorial-coverage bias rollup → notes/bias-report-YYYY-WW.md (P1-S13)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path

from psycopg.rows import dict_row

from app.db.connection import connection

_LOG = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_NOTES_DIR = _REPO_ROOT / "notes"

_ALL_CATEGORIES: tuple[str, ...] = (
    "macro",
    "rbi_policy",
    "regulatory",
    "india_specific",
    "geopolitical",
    "budget",
)


def _iso_week_label(when: datetime | None = None) -> str:
    ref = when or datetime.now(tz=UTC)
    year, week, _ = ref.isocalendar()
    return f"{year}-W{week:02d}"


def _report_path(when: datetime | None = None) -> Path:
    return _NOTES_DIR / f"bias-report-{_iso_week_label(when)}.md"


def fetch_editorial_coverage(*, days: int = 7) -> dict[str, int]:
    """Count published cards per event category in the trailing window."""
    stmt = """
    SELECT e.category::text AS category, COUNT(*)::int AS card_count
    FROM public.cards c
    INNER JOIN public.events e ON e.id = c.event_id
    WHERE c.lifecycle_state::text IN (
      'published', 'active', 'signal_triggered',
      'thesis_confirmed', 'thesis_weakened', 'resolved'
    )
      AND c.created_at >= now() - make_interval(days => %s)
    GROUP BY e.category
    ORDER BY card_count DESC, category
    """
    counts: dict[str, int] = {cat: 0 for cat in _ALL_CATEGORIES}
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(stmt, (days,))
        for row in cur.fetchall():
            counts[str(row["category"])] = int(row["card_count"])
    return counts


def render_report_markdown(
    counts: dict[str, int],
    *,
    generated_at: datetime | None = None,
    window_days: int = 7,
) -> str:
    when = generated_at or datetime.now(tz=UTC)
    covered = [c for c, n in counts.items() if n > 0]
    uncovered = [c for c in _ALL_CATEGORIES if counts.get(c, 0) == 0]
    lines = [
        f"# FinnWise editorial coverage — {_iso_week_label(when)}",
        "",
        f"_Generated {when.isoformat()} · trailing {window_days} days_",
        "",
        "## Categories with published cards",
        "",
    ]
    if covered:
        for cat in covered:
            label = cat.replace("_", " ")
            lines.append(f"- **{label}** — {counts[cat]} card(s)")
    else:
        lines.append("- _None in this window._")
    lines.extend(
        [
            "",
            "## Categories not covered (editorial coverage bias watch)",
            "",
        ]
    )
    if uncovered:
        for cat in uncovered:
            lines.append(f"- {cat.replace('_', ' ')}")
    else:
        lines.append("- _All monitored categories received at least one card._")
    lines.extend(
        [
            "",
            "## Note",
            "",
            (
                "This report tracks **editorial coverage bias** (PRD §6.5) — which event "
                "categories FinnWise chose to cover versus omit in the period. Per-card "
                "flags for recency, sector concentration, narrative, survivorship, and "
                "anchoring live in `card_bias_flags`."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def write_weekly_report(*, days: int = 7) -> Path:
    counts = fetch_editorial_coverage(days=days)
    body = render_report_markdown(counts, window_days=days)
    path = _report_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    try:
        path = write_weekly_report()
        _LOG.info("weekly_bias_report wrote %s", path)
    except Exception:
        _LOG.exception("weekly_bias_report failed")
        raise


if __name__ == "__main__":
    main()
