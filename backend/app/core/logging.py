"""Structured JSON logging for pipeline and ops events (P2-S13)."""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any


class JsonLogFormatter(logging.Formatter):
    """Emit one JSON object per log line for hosted log ingestion."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        event = getattr(record, "event", None)
        if event:
            payload["event"] = event
        for key, value in record.__dict__.items():
            if key.startswith("_") or key in {
                "name",
                "msg",
                "args",
                "levelname",
                "levelno",
                "pathname",
                "filename",
                "module",
                "exc_info",
                "exc_text",
                "stack_info",
                "lineno",
                "funcName",
                "created",
                "msecs",
                "relativeCreated",
                "thread",
                "threadName",
                "processName",
                "process",
                "message",
                "event",
            }:
                continue
            if key in payload:
                continue
            payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, separators=(",", ":"))


def configure_structured_logging() -> None:
    """Configure root logger once with JSON formatter (idempotent)."""
    root = logging.getLogger()
    if any(isinstance(h.formatter, JsonLogFormatter) for h in root.handlers):
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter())
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)


def log_event(event: str, fields: dict[str, Any], *, level: int = logging.INFO) -> None:
    """Log a structured event; fields are merged into the JSON payload."""
    configure_structured_logging()
    logging.getLogger("finnwise").log(level, event, extra={"event": event, **fields})


__all__ = ["JsonLogFormatter", "configure_structured_logging", "log_event"]
