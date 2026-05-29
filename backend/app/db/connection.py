"""Supabase Postgres connection for read paths (factor DB queries)."""

from __future__ import annotations

import os
import time
from collections.abc import Generator
from contextlib import contextmanager
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from psycopg import Connection
from psycopg import Error as PsycopgError
from psycopg_pool import ConnectionPool

from app.core.settings import get_settings
from app.diagnostics.timing import record_db_connect, record_db_query

_DB_URL_HINT = (
    "SUPABASE_DB_URL must be a full PostgreSQL URI "
    "(postgresql://postgres:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres). "
    "For Render and other IPv4 hosts, use the Supabase Session pooler URI instead "
    "(…pooler.supabase.com:5432/postgres) from Project Settings → Database → Connect."
)

_pool: ConnectionPool | None = None


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

    parsed = urlparse(normalized)
    host = (parsed.hostname or "").lower()
    # On Render (IPv4 egress), direct db.<ref>.supabase.co often fails or is slow.
    # Prefer the Supabase Session pooler URI (…pooler.supabase.com:5432/postgres).
    if (
        os.environ.get("RENDER") or os.environ.get("RENDER_SERVICE_ID")
    ) and host.endswith(".supabase.co") and "pooler.supabase.com" not in host:
        raise RuntimeError(
            "SUPABASE_DB_URL must use the Supabase Session pooler URI on Render "
            "(…pooler.supabase.com:5432/postgres)."
        )
    return normalized


def init_db_pool() -> None:
    """Create the shared connection pool (FastAPI lifespan startup or lazy first use)."""
    global _pool
    if _pool is not None:
        return

    raw_url = get_settings().supabase_db_url.strip()
    if not raw_url:
        return

    normalized = prepare_db_url(raw_url)
    if not normalized.startswith(("postgresql://", "postgres://")):
        return

    _pool = ConnectionPool(
        conninfo=normalized,
        kwargs=_connect_kwargs(normalized),
        min_size=1,
        max_size=10,
        open=True,
        name="finnwise",
    )


def close_db_pool() -> None:
    """Close the shared connection pool (FastAPI lifespan shutdown)."""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None


def _get_pool() -> ConnectionPool:
    if _pool is None:
        init_db_pool()
    if _pool is None:
        raise RuntimeError("SUPABASE_DB_URL is not configured")
    return _pool


@contextmanager
def connection() -> Generator[Connection, None, None]:
    _require_db_url(get_settings().supabase_db_url)
    pool = _get_pool()
    connect_start = time.perf_counter()
    try:
        with pool.connection() as conn:
            record_db_connect((time.perf_counter() - connect_start) * 1000)
            query_start = time.perf_counter()
            try:
                yield conn
            finally:
                record_db_query((time.perf_counter() - query_start) * 1000)
    except PsycopgError as exc:
        raise RuntimeError(f"SUPABASE_DB_URL connection failed: {exc}") from exc
