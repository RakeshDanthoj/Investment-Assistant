#!/usr/bin/env python3
"""Apply backend/db/migrations to the Supabase Postgres database."""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "backend"))

import psycopg  # noqa: E402

from app.core.settings import get_settings  # noqa: E402
from app.db.migrate import apply_migrations  # noqa: E402


def main() -> int:
    settings = get_settings()
    if not settings.supabase_db_url:
        print(
            "SUPABASE_DB_URL is not set in .env.local "
            "(Postgres connection string from Supabase dashboard).",
            file=sys.stderr,
        )
        return 1

    try:
        with psycopg.connect(settings.supabase_db_url) as conn:
            apply_migrations(conn)
    except psycopg.OperationalError as exc:
        err = str(exc).lower()
        print(f"Database connection failed: {exc}", file=sys.stderr)
        if "getaddrinfo" in err or "11001" in err:
            print(
                "\nDNS lookup failed for the database host. Typical causes: no internet, "
                "VPN off when required, corporate DNS/firewall blocking outbound DNS, or a "
                "typo in SUPABASE_DB_URL (Project Settings → Database → connection string).",
                file=sys.stderr,
            )
        return 1

    print("Migrations applied successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
