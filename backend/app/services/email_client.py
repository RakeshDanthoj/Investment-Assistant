"""Provider-agnostic transactional email (P2-S10)."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Literal

import httpx

from app.core.settings import get_settings

_LOG = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "email-templates"
_VAR_PATTERN = re.compile(r"\{\{\s*(\w+)\s*\}\}")

ProviderName = Literal["resend", "postmark"]


class EmailDeliveryError(RuntimeError):
    """Raised when the configured provider rejects a send."""


def render_template(template_name: str, variables: dict[str, str]) -> str:
    path = _TEMPLATES_DIR / template_name
    if not path.is_file():
        raise FileNotFoundError(f"Email template not found: {path}")
    html = path.read_text(encoding="utf-8")

    def _replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in variables:
            raise KeyError(f"Missing template variable: {key}")
        return variables[key]

    return _VAR_PATTERN.sub(_replace, html)


def _resolve_public_url() -> str:
    settings = get_settings()
    explicit = settings.app_public_url.strip().rstrip("/")
    if explicit:
        return explicit
    first_origin = settings.cors_origins.split(",")[0].strip().rstrip("/")
    return first_origin or "http://localhost:3000"


def _provider() -> ProviderName | None:
    raw = get_settings().email_provider.strip().lower()
    if raw in ("resend", "postmark"):
        return raw  # type: ignore[return-value]
    return None


def email_configured() -> bool:
    settings = get_settings()
    return bool(_provider() and settings.email_api_key.strip() and settings.email_from.strip())


def send(
    *,
    template: str,
    to: str,
    subject: str,
    variables: dict[str, str],
) -> bool:
    """
    Send a templated HTML email. Returns False when email is not configured (no-op).
    Raises EmailDeliveryError on provider failure.
    """
    settings = get_settings()
    provider = _provider()
    api_key = settings.email_api_key.strip()
    from_addr = settings.email_from.strip()

    if not provider or not api_key or not from_addr:
        _LOG.info(
            "email.send.skipped_unconfigured",
            extra={"template": template, "to_domain": to.split("@")[-1] if "@" in to else "unknown"},
        )
        return False

    html = render_template(template, variables)

    if provider == "resend":
        _send_resend(api_key=api_key, from_addr=from_addr, to=to, subject=subject, html=html)
    else:
        _send_postmark(api_key=api_key, from_addr=from_addr, to=to, subject=subject, html=html)

    return True


def _send_resend(*, api_key: str, from_addr: str, to: str, subject: str, html: str) -> None:
    payload = {"from": from_addr, "to": [to], "subject": subject, "html": html}
    with httpx.Client(timeout=20.0) as client:
        response = client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
        )
    if response.status_code >= 400:
        raise EmailDeliveryError(f"Resend error {response.status_code}: {response.text[:500]}")


def _send_postmark(*, api_key: str, from_addr: str, to: str, subject: str, html: str) -> None:
    payload = {"From": from_addr, "To": to, "Subject": subject, "HtmlBody": html}
    with httpx.Client(timeout=20.0) as client:
        response = client.post(
            "https://api.postmarkapp.com/email",
            headers={"X-Postmark-Server-Token": api_key},
            json=payload,
        )
    if response.status_code >= 400:
        raise EmailDeliveryError(f"Postmark error {response.status_code}: {response.text[:500]}")


__all__ = [
    "EmailDeliveryError",
    "email_configured",
    "render_template",
    "send",
    "_resolve_public_url",
]
