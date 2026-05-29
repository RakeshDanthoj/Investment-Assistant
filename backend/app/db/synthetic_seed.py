"""Idempotent synthetic historical event seed (P3-S0 / G-13)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from psycopg.rows import dict_row

from app.db.connection import connection
from app.db.migrate import apply_migrations

DEFAULT_FIXTURE = (
    Path(__file__).resolve().parents[2] / "scripts" / "seed_data" / "synthetic_events.json"
)
EVENT_SOURCE = "synthetic_seed"
PROMPT_VERSION = "synthetic-seed-v1"

UPSERT_SQL = """
INSERT INTO public.events (
  external_id,
  title,
  category,
  source_url,
  canonical_url,
  event_source,
  confidence_score,
  confidence_raw,
  confidence_effective,
  lifecycle_state,
  is_synthetic,
  is_major,
  created_at,
  prompt_version
)
VALUES (
  %s, %s, %s::public.event_category, %s, %s, %s,
  %s, %s, %s, %s::public.lifecycle_state, TRUE, %s, %s, %s
)
ON CONFLICT (external_id) WHERE external_id IS NOT NULL
DO UPDATE SET
  title = EXCLUDED.title,
  category = EXCLUDED.category,
  source_url = EXCLUDED.source_url,
  canonical_url = EXCLUDED.canonical_url,
  event_source = EXCLUDED.event_source,
  confidence_score = EXCLUDED.confidence_score,
  confidence_raw = EXCLUDED.confidence_raw,
  confidence_effective = EXCLUDED.confidence_effective,
  lifecycle_state = EXCLUDED.lifecycle_state,
  is_synthetic = TRUE,
  is_major = EXCLUDED.is_major,
  created_at = EXCLUDED.created_at,
  prompt_version = EXCLUDED.prompt_version
RETURNING (xmax = 0) AS inserted
"""


def load_fixture(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("synthetic_events.json must be a JSON array")
    return data


def _parse_occurred_at(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return datetime.fromisoformat(text)


def _confidence_score(raw: float) -> int:
    return max(0, min(100, int(round(float(raw) * 100))))


def seed_events(*, fixture_path: Path = DEFAULT_FIXTURE, apply_migration: bool = True) -> dict[str, int]:
    rows = load_fixture(fixture_path)
    if len(rows) != 20:
        raise ValueError(f"expected 20 synthetic events, got {len(rows)}")

    major_count = sum(1 for r in rows if r.get("is_major"))
    if major_count != 7:
        raise ValueError(f"expected 7 is_major events, got {major_count}")

    inserted = 0
    updated = 0

    with connection() as conn:
        if apply_migration:
            apply_migrations(conn)
        with conn.cursor(row_factory=dict_row) as cur:
            for row in rows:
                external_id = str(row["external_id"])
                canonical_url = f"synthetic://seed/{external_id}"
                source_url = str(row.get("source_url") or canonical_url)[:3800]
                occurred_at = _parse_occurred_at(str(row["occurred_at"]))
                raw = float(row["confidence_raw"])
                effective = float(row.get("confidence_effective", raw))
                params = (
                    external_id,
                    str(row["title"])[:3800],
                    str(row["category"]),
                    source_url,
                    canonical_url,
                    EVENT_SOURCE,
                    _confidence_score(raw),
                    raw,
                    effective,
                    str(row.get("lifecycle_state") or "resolved"),
                    bool(row.get("is_major")),
                    occurred_at,
                    PROMPT_VERSION,
                )
                cur.execute(UPSERT_SQL, params)
                result = cur.fetchone()
                if result and result.get("inserted"):
                    inserted += 1
                else:
                    updated += 1
        conn.commit()

    return {"inserted": inserted, "updated": updated, "total": len(rows)}
