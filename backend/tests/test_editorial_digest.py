"""P3-S1e: Sunday digest sections cap at 10 items each."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.db.migrate import apply_migrations
from app.services.editorial_digest import (
    build_watchlist_and_dedup_sections,
    render_editorial_digest_html,
)


@pytest.mark.integration
def test_digest_sections_include_counts(db_connection) -> None:
    apply_migrations(db_connection)
    from contextlib import contextmanager

    @contextmanager
    def _use_conn():
        yield db_connection

    with (
        patch("app.services.watchlist.connection", side_effect=_use_conn),
        patch("app.services.editorial_digest.connection", side_effect=_use_conn),
    ):
        sections = build_watchlist_and_dedup_sections(cap=10)

    assert "watchlist_section_html" in sections
    assert "dedup_section_html" in sections
    assert int(sections["watchlist_count"]) <= 10
    assert int(sections["dedup_count"]) <= 10
    assert "/editor/watchlist" in sections["watchlist_url"]


def test_render_editorial_digest_html_has_sections() -> None:
    with patch(
        "app.services.editorial_digest.build_watchlist_and_dedup_sections",
        return_value={
            "watchlist_section_html": "<ul><li>macro: test</li></ul>",
            "dedup_section_html": "<p>None pending.</p>",
            "watchlist_count": "1",
            "dedup_count": "0",
            "watchlist_url": "http://localhost:3000/editor/watchlist",
        },
    ):
        html = render_editorial_digest_html()
    assert "Slow-burn watchlist" in html
    assert "Dedup review queue" in html
    assert "macro: test" in html
