"""Apply SQL seeds from `backend/db/seeds/` (dev + integration tests)."""

from __future__ import annotations

from pathlib import Path

SEEDS_DIR = Path(__file__).resolve().parents[2] / "db" / "seeds"


def apply_banking_sector_seed(connection) -> None:
    path = SEEDS_DIR / "banking_sector.sql"
    sql = path.read_text(encoding="utf-8")
    with connection.cursor() as cur:
        cur.execute(sql)
