"""Request-scoped DB timing for latency diagnostics (P1.5-S1)."""

from __future__ import annotations

import json
import time
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


@dataclass
class DbTimingAccumulator:
    db_connect_ms: float = 0.0
    db_query_ms: float = 0.0
    connection_count: int = 0

    def reset(self) -> None:
        self.db_connect_ms = 0.0
        self.db_query_ms = 0.0
        self.connection_count = 0


_db_timing: ContextVar[DbTimingAccumulator | None] = ContextVar("_db_timing", default=None)


def record_db_connect(connect_ms: float) -> None:
    acc = _db_timing.get()
    if acc is not None:
        acc.db_connect_ms += connect_ms
        acc.connection_count += 1


def record_db_query(query_ms: float) -> None:
    acc = _db_timing.get()
    if acc is not None:
        acc.db_query_ms += query_ms


@dataclass
class DbRequestTimer:
    started_at: float = field(default_factory=time.perf_counter)
    accumulator: DbTimingAccumulator = field(default_factory=DbTimingAccumulator)
    _token: Any = field(default=None, repr=False)

    def __enter__(self) -> DbRequestTimer:
        self.accumulator.reset()
        self.started_at = time.perf_counter()
        self._token = _db_timing.set(self.accumulator)
        return self

    def __exit__(self, *_args: object) -> None:
        if self._token is not None:
            _db_timing.reset(self._token)

    @property
    def total_ms(self) -> float:
        return (time.perf_counter() - self.started_at) * 1000

    def snapshot(self) -> dict[str, float | int]:
        return {
            "db_connect_ms": round(self.accumulator.db_connect_ms, 2),
            "db_query_ms": round(self.accumulator.db_query_ms, 2),
            "total_ms": round(self.total_ms, 2),
            "connection_count": self.accumulator.connection_count,
        }


def timing_headers(snapshot: dict[str, float | int]) -> dict[str, str]:
    connect = float(snapshot["db_connect_ms"])
    query = float(snapshot["db_query_ms"])
    total = float(snapshot["total_ms"])
    server_timing = (
        f"db_connect;dur={connect}, db_query;dur={query}, total;dur={total}"
    )
    payload: dict[str, float | int] = {
        "db_connect_ms": connect,
        "db_query_ms": query,
        "total_ms": total,
    }
    if "connection_count" in snapshot:
        payload["connection_count"] = int(snapshot["connection_count"])
    return {
        "Server-Timing": server_timing,
        "X-FinnWise-Timing": json.dumps(payload, separators=(",", ":")),
    }


def json_response_with_timing(
    content: Any,
    timer: DbRequestTimer,
    *,
    status_code: int = 200,
) -> JSONResponse:
    return JSONResponse(
        content=jsonable_encoder(content),
        status_code=status_code,
        headers=timing_headers(timer.snapshot()),
    )
