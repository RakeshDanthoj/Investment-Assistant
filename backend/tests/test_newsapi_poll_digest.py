"""P3-S1d: NewsAPI poll summary in editorial digest template."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import patch

from app.services.editorial_digest import (
    editorial_digest_template_variables,
    format_newsapi_poll_summary_html,
)
from app.services.email_client import render_template
from app.services.factor_poll_log import FactorPollRow


def test_format_poll_summary_empty() -> None:
    with patch("app.services.editorial_digest.recent_factor_polls", return_value=[]):
        html = format_newsapi_poll_summary_html()
    assert "No NewsAPI factor polls" in html


def test_render_editorial_digest_includes_poll_row() -> None:
    polled = datetime(2026, 5, 30, 8, 0, tzinfo=UTC)
    row = FactorPollRow(
        slug="crude_oil",
        display_name="Crude oil price",
        polled_at=polled,
        status="ok",
        article_count=12,
    )
    with (
        patch("app.services.editorial_digest.recent_factor_polls", return_value=[row]),
        patch(
            "app.services.editorial_digest.build_watchlist_and_dedup_sections",
            return_value={
                "watchlist_section_html": "<p>None pending.</p>",
                "dedup_section_html": "<p>None pending.</p>",
                "watchlist_count": "0",
                "dedup_count": "0",
                "watchlist_url": "http://localhost:3000/editor/watchlist",
            },
        ),
    ):
        variables = editorial_digest_template_variables()
    html = render_template("editorial_digest.html", variables)
    assert "Crude oil price" in html
    assert "ok" in html
    assert "12" in html
