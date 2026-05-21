"""Parse CORS_ORIGINS into FastAPI CORSMiddleware allow lists."""

from __future__ import annotations

import re


def parse_cors_origins(cors_origins: str) -> tuple[list[str], str | None]:
    """
    Split comma-separated origins into exact matches and a combined regex.

    Entries containing ``*`` become regex fragments (``*`` → ``[^/]+``).
    Example: ``https://*.vercel.app`` → ``^https://[^/]+\\.vercel\\.app$``
    """
    exact: list[str] = []
    patterns: list[str] = []

    for part in cors_origins.split(","):
        origin = part.strip()
        if not origin:
            continue
        if "*" in origin:
            escaped = re.escape(origin).replace(r"\*", "[^/]+")
            patterns.append(f"^{escaped}$")
        else:
            exact.append(origin)

    combined_regex: str | None = None
    if patterns:
        combined_regex = "|".join(f"(?:{p})" for p in patterns)

    return exact, combined_regex
