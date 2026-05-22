"""Supabase Postgres connection for read paths (factor DB queries)."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import psycopg
from psycopg import Connection, Error as PsycopgError

from app.core.settings import get_settings

_DB_URL_HINT = (
    "SUPABASE_DB_URL must be a full PostgreSQL URI "
    "(postgresql://postgres:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres). "
    "For Render and other IPv4 hosts, use the Supabase Session pooler URI instead "
    "(…pooler.supabase.com:5432/postgres) from Project Settings → Database → Connect."
)


def _strip_wrapping_quotes(value: str) -> str:
    text = value.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        return text[1:-1].strip()
    return text


def prepare_db_url(url: str) -> str:
    """Normalize env-provided Postgres URI for Supabase + external hosts (e.g. Render)."""
    normalized = _strip_wrapping_quotes(url)
    if not normalized:
        return ""
    if not normalized.startswith(("postgresql://", "postgres://")):
        return normalized

    parsed = urlparse(normalized)
    host = (parsed.hostname or "").lower()
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))

    if "supabase.co" in host or "pooler.supabase.com" in host:
        query.setdefault("sslmode", "require")

    rebuilt = urlunparse(parsed._replace(query=urlencode(query)))
    return rebuilt


def _connect_kwargs(url: str) -> dict[str, object]:
    parsed = urlparse(url)
    port = parsed.port or 5432
    kwargs: dict[str, object] = {"connect_timeout": 10}
    # Transaction pooler (6543) does not support prepared statements.
    if port == 6543:
        kwargs["prepare_threshold"] = None
    return kwargs


def _require_db_url(url: str) -> str:
    normalized = prepare_db_url(url)
    if not normalized:
        raise RuntimeError("SUPABASE_DB_URL is not configured")
    if not normalized.startswith(("postgresql://", "postgres://")):
        raise RuntimeError(_DB_URL_HINT)
    return normalized


@contextmanager
def connection() -> Generator[Connection, None, None]:
    url = _require_db_url(get_settings().supabase_db_url)
    try:
        conn = psycopg.connect(url, **_connect_kwargs(url))
    except PsycopgError as exc:
        raise RuntimeError(f"SUPABASE_DB_URL connection failed: {exc}") from exc
    try:
        yield conn
    finally:
        conn.close()
