"""Parse NSE disclosure timestamps into timezone-aware datetimes."""

from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

_IST = ZoneInfo("Asia/Kolkata")

_NSE_DT_FORMATS = (
    "%d-%b-%Y %H:%M:%S",
    "%d-%b-%Y %H:%M",
    "%d-%b-%Y",
    "%d-%m-%Y %H:%M:%S",
    "%d-%m-%Y",
)


def parse_nse_observed_at(raw: str | None) -> datetime | None:
    """Best-effort parse for ``an_dt`` / ``broadcast_dttm`` style strings (IST wall clock)."""
    if not raw or not str(raw).strip():
        return None
    text = str(raw).strip()
    for fmt in _NSE_DT_FORMATS:
        try:
            naive = datetime.strptime(text, fmt)
            return naive.replace(tzinfo=_IST).astimezone(UTC)
        except ValueError:
            continue
    return None
