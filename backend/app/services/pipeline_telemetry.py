"""Persist pipeline run telemetry for admin metrics (P2-S13)."""

from __future__ import annotations

import json
import logging
from typing import Any

from psycopg.rows import dict_row

from app.core.logging import log_event
from app.db.connection import connection

_LOG = logging.getLogger(__name__)


def record_pipeline_run(
    *,
    pipeline: str,
    prompt_version: str,
    input_tokens: int,
    output_tokens: int,
    duration_ms: int,
    status: str = "ok",
    error_message: str | None = None,
    context: dict[str, Any] | None = None,
) -> None:
    """Write structured JSON log line and append-only DB row."""
    ctx = context or {}
    log_event(
        "pipeline.run",
        {
            "pipeline": pipeline,
            "prompt_version": prompt_version,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "duration_ms": duration_ms,
            "status": status,
            "error_message": error_message,
            **ctx,
        },
        level=40 if status == "error" else 20,
    )

    try:
        with connection() as conn, conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                INSERT INTO public.pipeline_runs (
                  pipeline, prompt_version, input_tokens, output_tokens,
                  duration_ms, status, error_message, context
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                """,
                (
                    pipeline,
                    prompt_version,
                    input_tokens,
                    output_tokens,
                    duration_ms,
                    status,
                    error_message,
                    json.dumps(ctx),
                ),
            )
            conn.commit()
    except Exception as exc:  # noqa: BLE001 — telemetry must not break pipelines
        _LOG.warning(
            "pipeline_telemetry.persist_failed",
            extra={"pipeline": pipeline, "error": str(exc)},
        )


__all__ = ["record_pipeline_run"]
