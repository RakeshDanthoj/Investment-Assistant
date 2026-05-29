"""Sunday editorial digest email variables (P3-S1d poll log + P3-S1e watchlist/dedup)."""

from __future__ import annotations

import html
from datetime import UTC, datetime
from typing import Any

from psycopg.rows import dict_row

from app.db.connection import connection
from app.services.email_client import _resolve_public_url, render_template, send_html
from app.services.factor_poll_log import recent_factor_polls
from app.services.watchlist import list_watchlist_items

_DIGEST_CAP = 10


def format_newsapi_poll_summary_html() -> str:
    """Render recent factor poll rows for ``editorial_digest.html`` (log-only fields)."""
    polls = recent_factor_polls(limit=8)
    if not polls:
        return (
            "<p style='margin:0;font-size:13px;color:#6b6b6b;'>"
            "No NewsAPI factor polls recorded yet.</p>"
        )

    lines: list[str] = [
        "<table role='presentation' width='100%' cellpadding='0' cellspacing='0' "
        "style='font-size:13px;border-collapse:collapse;'>",
        "<tr style='background:#f4f1ec;'>"
        "<th align='left' style='padding:6px 8px;'>Factor</th>"
        "<th align='left' style='padding:6px 8px;'>Status</th>"
        "<th align='right' style='padding:6px 8px;'>Articles</th>"
        "<th align='left' style='padding:6px 8px;'>Polled (UTC)</th>"
        "</tr>",
    ]
    for row in polls:
        polled = row.polled_at.astimezone().strftime("%Y-%m-%d %H:%M")
        lines.append(
            "<tr>"
            f"<td style='padding:6px 8px;border-top:1px solid #e5e0d8;'>{row.display_name}</td>"
            f"<td style='padding:6px 8px;border-top:1px solid #e5e0d8;'>{row.status}</td>"
            f"<td align='right' style='padding:6px 8px;border-top:1px solid #e5e0d8;'>"
            f"{row.article_count}</td>"
            f"<td style='padding:6px 8px;border-top:1px solid #e5e0d8;'>{polled}</td>"
            "</tr>"
        )
    lines.append("</table>")
    return "\n".join(lines)


def _list_pending_dedup_reviews(limit: int = _DIGEST_CAP) -> list[dict[str, Any]]:
    lim = max(1, min(limit, _DIGEST_CAP))
    sql = """
    SELECT id, event_ids, reason, status, created_at
    FROM public.dedup_review_queue
    WHERE status = 'pending'
    ORDER BY created_at DESC
    LIMIT %s
    """
    with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
        cur.execute(sql, (lim,))
        rows = cur.fetchall()
    out: list[dict[str, Any]] = []
    for row in rows:
        created = row["created_at"]
        out.append(
            {
                "id": str(row["id"]),
                "event_ids": [str(e) for e in (row.get("event_ids") or [])],
                "reason": str(row.get("reason") or ""),
                "created_at": created.isoformat()
                if hasattr(created, "isoformat")
                else str(created),
            }
        )
    return out


def _html_list(items: list[str]) -> str:
    if not items:
        return "<p style='margin:0;font-size:13px;color:#6b6b6b;'>None pending.</p>"
    lis = "".join(
        f"<li style='margin:0 0 8px;font-size:14px;line-height:1.45;'>{html.escape(line)}</li>"
        for line in items
    )
    return f"<ul style='margin:0;padding-left:20px;'>{lis}</ul>"


def build_watchlist_and_dedup_sections(*, cap: int = _DIGEST_CAP) -> dict[str, str]:
    """HTML fragments for watchlist + dedup review (max `cap` each)."""
    watch_rows = list_watchlist_items(status="watching", limit=cap)
    watch_lines = [
        f"{row['category']}: {row['event_description'][:160]}"
        + (
            f" — trigger: {row['escalation_trigger'][:80]}"
            if row.get("escalation_trigger")
            else ""
        )
        for row in watch_rows
    ]

    dedup_rows = _list_pending_dedup_reviews(limit=cap)
    dedup_lines = [
        f"{row['reason']} ({len(row['event_ids'])} events, queued {row['created_at'][:10]})"
        for row in dedup_rows
    ]

    base = _resolve_public_url().rstrip("/")
    return {
        "watchlist_section_html": _html_list(watch_lines),
        "dedup_section_html": _html_list(dedup_lines),
        "watchlist_count": str(len(watch_lines)),
        "dedup_count": str(len(dedup_lines)),
        "watchlist_url": f"{base}/editor/watchlist",
    }


def editorial_digest_template_variables() -> dict[str, str]:
    variables = {
        "digest_date": datetime.now(tz=UTC).strftime("%d %b %Y"),
        "newsapi_poll_summary": format_newsapi_poll_summary_html(),
    }
    variables.update(build_watchlist_and_dedup_sections())
    return variables


def render_editorial_digest_html() -> str:
    return render_template("editorial_digest.html", editorial_digest_template_variables())


def send_editorial_digest(*, to: str, subject: str | None = None) -> bool:
    """Send Sunday digest to Product Owner inbox. No-op when email is not configured."""
    subj = subject or "FinnWise — Sunday editorial digest"
    return send_html(to=to, subject=subj, html=render_editorial_digest_html())
