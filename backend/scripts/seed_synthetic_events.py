#!/usr/bin/env python3
"""CLI entrypoint for synthetic historical event seed (P3-S0 / G-13)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

def main() -> int:
    from app.db.synthetic_seed import DEFAULT_FIXTURE, seed_events

    parser = argparse.ArgumentParser(description="Seed synthetic Phase 3 historical events.")
    parser.add_argument(
        "--fixture",
        type=Path,
        default=DEFAULT_FIXTURE,
        help="Path to synthetic_events.json",
    )
    parser.add_argument(
        "--skip-migration",
        action="store_true",
        help="Assume 0021_synthetic_isolation.sql is already applied",
    )
    args = parser.parse_args()

    try:
        stats = seed_events(
            fixture_path=args.fixture,
            apply_migration=not args.skip_migration,
        )
    except Exception as exc:
        print(f"seed failed: {exc}", file=sys.stderr)
        return 1

    print(
        f"seed complete: {stats['total']} events "
        f"({stats['inserted']} inserted, {stats['updated']} updated on conflict)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
