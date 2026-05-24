"""Apply SQL seeds from `backend/db/seeds/` (dev + integration tests)."""

from __future__ import annotations

from pathlib import Path

SEEDS_DIR = Path(__file__).resolve().parents[2] / "db" / "seeds"
SECTORS_DIR = SEEDS_DIR / "sectors"

SECTOR_SEED_FILES = (
    "it.sql",
    "energy.sql",
    "fmcg.sql",
    "auto.sql",
    "pharma.sql",
    "metals.sql",
    "telecom.sql",
    "infra.sql",
)


def _execute_sql_file(connection, path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    with connection.cursor() as cur:
        cur.execute(sql)


def apply_banking_sector_seed(connection) -> None:
    _execute_sql_file(connection, SEEDS_DIR / "banking_sector.sql")


def apply_phase2_sector_seeds(connection) -> None:
    for name in SECTOR_SEED_FILES:
        _execute_sql_file(connection, SECTORS_DIR / name)


def apply_map_modules_seed(connection) -> None:
    _execute_sql_file(connection, SEEDS_DIR / "map_modules.sql")


def apply_all_factor_db_seeds(connection) -> None:
    """Banking (P1-S5) + seven Phase 2 sectors + Map modules (P2-S11)."""
    apply_banking_sector_seed(connection)
    apply_phase2_sector_seeds(connection)
    apply_map_modules_seed(connection)
