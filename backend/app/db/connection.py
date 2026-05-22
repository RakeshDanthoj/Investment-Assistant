"""Supabase Postgres connection for read paths (factor DB queries)."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

import psycopg
from psycopg import Connection

from app.core.settings import get_settings


@contextmanager
def connection() -> Generator[Connection, None, None]:
    url = get_settings().supabase_db_url.strip()
    if not url:
        raise RuntimeError("SUPABASE_DB_URL is not configured")
    conn = psycopg.connect(url)
    try:
        yield conn
    finally:
        conn.close()
