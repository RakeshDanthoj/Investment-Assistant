"""P3-S1c / G-03: dedup_key computation, merge upsert, and cross-category review queue."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any
from uuid import UUID

import yaml
from psycopg.rows import dict_row

from app.core.settings import get_settings
from app.db.connection import connection
from app.models.enums import EventCategory, LifecycleState
from app.services.confidence_scorer import apply_confidence_to_event_row
from app.sources.base import AdapterSource, RawEvent, utc_now

_LOG = logging.getLogger(__name__)

_ENTITY_MAP_PATH = Path(__file__).resolve().parent.parent / "config" / "entity_map.yaml"
_WINDOW_SECONDS = 4 * 3600
_FORCE_REVIEW_SOURCE_THRESHOLD = 5

UPSERT_SQL = """
INSERT INTO public.events (
  title,
  category,
  event_source,
  canonical_url,
  source_url,
  confidence_score,
  confidence_raw,
  lifecycle_state,
  dedup_key,
  collision_fingerprint,
  source_count,
  sources,
  force_editorial_review,
  created_at
)
VALUES (
  %s, %s::public.event_category, %s, %s, %s,
  %s, %s, %s::public.lifecycle_state,
  %s, %s, 1, %s::jsonb, %s, COALESCE(%s, now())
)
ON CONFLICT (dedup_key) WHERE dedup_key IS NOT NULL
DO UPDATE SET
  source_count = public.events.source_count + 1,
  sources = public.events.sources || EXCLUDED.sources,
  confidence_score = GREATEST(public.events.confidence_score, EXCLUDED.confidence_score)
RETURNING id, (xmax = 0) AS inserted, source_count, title, category::text AS category,
  event_source, canonical_url, sources, created_at
"""


def normalise_headline(text: str) -> str:
    """Lowercase, collapse whitespace, strip punctuation; cap at 100 chars."""
    lower = text.lower().strip()
    collapsed = re.sub(r"\s+", " ", lower)
    cleaned = re.sub(r"[^\w\s]", "", collapsed)
    return cleaned[:100]


def headline_hash(text: str) -> str:
    """Normalised first 100 chars — dedup key component for all categories (G-03 PO)."""
    return normalise_headline(text)


def floor_to_4h(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    epoch = int(dt.timestamp())
    floored = (epoch // _WINDOW_SECONDS) * _WINDOW_SECONDS
    return datetime.fromtimestamp(floored, tz=UTC)


@lru_cache(maxsize=1)
def load_entity_map(path: Path | None = None) -> dict[str, str]:
    """Load alias → canonical slug map from YAML (longest alias match at lookup time)."""
    map_path = path or _ENTITY_MAP_PATH
    raw = yaml.safe_load(map_path.read_text(encoding="utf-8"))
    entities = raw.get("entities") if isinstance(raw, dict) else None
    if not isinstance(entities, dict):
        raise ValueError(f"{map_path}: expected top-level 'entities' mapping")
    return {str(k): str(v) for k, v in entities.items()}


def normalise_entity(
    headline: str,
    body: str | None,
    entity_map: dict[str, str] | None = None,
) -> str:
    """Return canonical entity slug from longest matching alias, or 'unknown'."""
    mapping = entity_map if entity_map is not None else load_entity_map()
    haystack = f"{headline} {body or ''}".lower()
    best_alias = ""
    best_slug = "unknown"
    for alias, slug in mapping.items():
        alias_lower = alias.lower()
        if alias_lower in haystack and len(alias) > len(best_alias):
            best_alias = alias
            best_slug = slug
    return best_slug


def compute_dedup_key(
    *,
    category: str | EventCategory,
    headline: str,
    body: str | None = None,
    detected_at: datetime,
    entity_map: dict[str, str] | None = None,
) -> str:
    """
    sha256(category | normalised_entity | 4h_window | headline_hash) for all categories.
    """
    cat = category.value if isinstance(category, EventCategory) else category
    entity = normalise_entity(headline, body, entity_map)
    window = floor_to_4h(detected_at)
    h_hash = headline_hash(headline)
    parts = [cat, entity, window.isoformat(), h_hash]
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return digest


def compute_collision_fingerprint(
    *,
    headline: str,
    body: str | None = None,
    detected_at: datetime,
    entity_map: dict[str, str] | None = None,
) -> str:
    """Category-agnostic fingerprint for cross-category collision detection."""
    entity = normalise_entity(headline, body, entity_map)
    window = floor_to_4h(detected_at)
    h_hash = headline_hash(headline)
    parts = [entity, window.isoformat(), h_hash]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()


def recompute_confidence_raw(*, source_count: int, confidence_score: int) -> float:
    """
    Deprecated interim helper — prefer :func:`confidence_scorer.compute_confidence`.

    Kept for unit tests that assert monotonicity with source_count before full scorer inputs.
    """
    score_norm = min(max(confidence_score, 0), 100) / 100.0
    source_factor = min(source_count / 3.0, 1.0)
    raw = 0.30 * source_factor + 0.70 * score_norm
    return round(min(raw, 1.0), 3)


def _source_entry(
    *,
    event_source: str,
    canonical_url: str,
    title: str,
    retrieved_at: datetime,
) -> dict[str, str]:
    return {
        "event_source": event_source,
        "canonical_url": canonical_url,
        "title": title[:500],
        "retrieved_at": retrieved_at.isoformat(),
    }


def _queue_cross_category_review(
    conn: Any,
    *,
    new_event_id: UUID,
    collision_fingerprint: str,
    category: str,
) -> None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT id FROM public.events
            WHERE collision_fingerprint = %s
              AND category::text <> %s
            LIMIT 5
            """,
            (collision_fingerprint, category),
        )
        peers = cur.fetchall()
        for peer in peers:
            peer_id = peer["id"]
            event_ids = sorted([str(new_event_id), str(peer_id)])
            cur.execute(
                """
                SELECT id FROM public.dedup_review_queue
                WHERE status = 'pending'
                  AND event_ids @> %s::uuid[]
                  AND event_ids <@ %s::uuid[]
                LIMIT 1
                """,
                (event_ids, event_ids),
            )
            if cur.fetchone():
                continue
            cur.execute(
                """
                INSERT INTO public.dedup_review_queue (event_ids, reason)
                VALUES (%s::uuid[], %s)
                """,
                (
                    event_ids,
                    "cross_category_same_window",
                ),
            )
            _LOG.info(
                "event_dedup.cross_category_queued",
                extra={"event_ids": event_ids, "fingerprint": collision_fingerprint},
            )


def persist_deduped_event(
    *,
    raw: RawEvent,
    title: str,
    category: EventCategory,
    event_source: AdapterSource | str,
    canonical_url: str,
    confidence_score: int,
    source_url: str | None = None,
    detected_at: datetime | None = None,
) -> str:
    """
    Dedup-aware insert/merge via Postgres.

    Returns ``inserted``, ``duplicate`` (merged), ``skipped_no_config``, or ``error``.
    """
    settings = get_settings()
    if not settings.supabase_db_url.strip():
        return "skipped_no_config"

    src = event_source.value if isinstance(event_source, AdapterSource) else event_source
    canonical_norm = canonical_url.strip()
    if not canonical_norm:
        return "skipped_no_config"

    detected = detected_at or raw.published_at or utc_now()
    body = raw.excerpt
    dedup_key = compute_dedup_key(
        category=category,
        headline=title,
        body=body,
        detected_at=detected,
    )
    collision_fp = compute_collision_fingerprint(
        headline=title,
        body=body,
        detected_at=detected,
    )
    retrieved = detected if detected.tzinfo else detected.replace(tzinfo=UTC)
    source_blob = json.dumps(
        [_source_entry(
            event_source=src,
            canonical_url=canonical_norm,
            title=title,
            retrieved_at=retrieved,
        )]
    )
    initial_raw = recompute_confidence_raw(source_count=1, confidence_score=confidence_score)

    row: dict[str, Any] | None = None
    try:
        with connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    UPSERT_SQL,
                    (
                        title[:3800],
                        category.value,
                        src,
                        canonical_norm[:3800],
                        (source_url or canonical_norm)[:3800],
                        confidence_score,
                        initial_raw,
                        LifecycleState.DRAFT.value,
                        dedup_key,
                        collision_fp,
                        source_blob,
                        False,
                        retrieved,
                    ),
                )
                row = cur.fetchone()
                if row:
                    sources_json = row["sources"]
                    if isinstance(sources_json, str):
                        sources_json = json.loads(sources_json)
                    apply_confidence_to_event_row(
                        cur,
                        event_id=row["id"],
                        title=str(row["title"]),
                        category=str(row["category"]),
                        event_source=str(row["event_source"] or src),
                        canonical_url=row.get("canonical_url"),
                        source_count=int(row["source_count"] or 1),
                        sources=list(sources_json or []),
                        first_seen_at=row["created_at"],
                        body=body,
                        reference=retrieved,
                    )
            if row and row["inserted"]:
                _queue_cross_category_review(
                    conn,
                    new_event_id=row["id"],
                    collision_fingerprint=collision_fp,
                    category=category.value,
                )
            conn.commit()
    except Exception as exc:
        _LOG.warning(
            "event_dedup.persist_failed",
            extra={"dedup_key": dedup_key, "error": repr(exc)},
        )
        return "error"

    if row is None:
        return "error"
    return "inserted" if row["inserted"] else "duplicate"


def clear_entity_map_cache() -> None:
    load_entity_map.cache_clear()
