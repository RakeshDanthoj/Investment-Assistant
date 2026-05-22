"""Weekly editorial-coverage bias report (P1-S13)."""

from __future__ import annotations

from app.jobs.weekly_bias_report import render_report_markdown


def test_render_report_lists_covered_and_uncovered_categories() -> None:
    counts = {
        "macro": 2,
        "rbi_policy": 0,
        "regulatory": 0,
        "india_specific": 1,
        "geopolitical": 0,
        "budget": 0,
    }
    md = render_report_markdown(counts, window_days=7)
    assert "macro" in md.lower() or "Macro" in md
    assert "not covered" in md.lower()
    assert "editorial coverage bias" in md.lower()
