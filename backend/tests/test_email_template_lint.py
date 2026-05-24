"""Email templates must not contain recommendation language (P2-S10)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from app.services.email_client import render_template

_FORBIDDEN = re.compile(r"\b(buy|sell|hold)\b", re.IGNORECASE)
_TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "email-templates"


@pytest.mark.parametrize(
    "filename",
    sorted(p.name for p in _TEMPLATES_DIR.glob("*.html")),
)
def test_template_source_has_no_forbidden_words(filename: str) -> None:
    text = (_TEMPLATES_DIR / filename).read_text(encoding="utf-8")
    assert not _FORBIDDEN.search(text), f"{filename} contains buy/sell/hold wording"


def test_rendered_signal_fired_template_has_no_forbidden_words() -> None:
    html = render_template(
        "signal_fired.html",
        {
            "card_title": "RBI policy watch",
            "thread_url": "https://app.example/thread/abc",
            "unsubscribe_url": "https://app.example/unsubscribe?token=xyz",
        },
    )
    assert not _FORBIDDEN.search(html)
    assert "unsubscribe" in html.lower()
