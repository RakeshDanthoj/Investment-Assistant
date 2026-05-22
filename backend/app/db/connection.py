"""Supabase Postgres connection for read paths (factor DB queries)."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

import psycopg
from psycopg import Connection, Error as PsycopgError

from app.core.settings import get_settings

_DB_URL_HINT = (
    "SUPABASE_DB_URL must be a full PostgreSQL URI "
    "(postgresql://postgres:PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres). "
    "A bare Supabase project ref is not valid."
)


def _require_db_url(url: str) -> str:
    normalized = url.strip()
    if not normalized:
        raise RuntimeError("SUPABASE_DB_URL is not configured")
    if not normalized.startswith(("postgresql://", "postgres://")):
        raise RuntimeError(_DB_URL_HINT)
    return normalized


@contextmanager
def connection() -> Generator[Connection, None, None]:
    url = _require_db_url(get_settings().supabase_db_url)
    try:
        conn = psycopg.connect(url)
    except PsycopgError as exc:
        raise RuntimeError(f"SUPABASE_DB_URL connection failed: {exc}") from exc
    try:
        yield conn
    finally:
        conn.close()
