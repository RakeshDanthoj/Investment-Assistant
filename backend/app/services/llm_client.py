"""Thin Google Gemini client (google-genai SDK) with retries + structured logging (P1-S7)."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from app.core.settings import get_settings

_LOG = logging.getLogger(__name__)

_REPO_PROMPTS = Path(__file__).resolve().parents[2] / "prompts"
_MAX_RETRIES = 4
_BACKOFF_BASE_S = 0.7


def _is_retryable_api_error(exc: BaseException) -> bool:
    if isinstance(exc, genai_errors.ServerError):
        return True
    if isinstance(exc, genai_errors.ClientError):
        code = getattr(exc, "status_code", None)
        return code in {408, 429, 500, 502, 503, 504}
    return isinstance(exc, genai_errors.APIError) and getattr(exc, "status_code", None) in {
        408,
        429,
        500,
        502,
        503,
        504,
    }


def load_prompt_markdown(rel_name: str) -> str:
    p = _REPO_PROMPTS / rel_name
    raw = p.read_text(encoding="utf-8")
    if raw.lstrip().startswith("---"):
        segments = raw.split("---", 2)
        if len(segments) >= 3:
            return segments[2].lstrip("\n")
    return raw


def render_prompt(template: str, variables: dict[str, str]) -> str:
    out = template
    for k, v in variables.items():
        out = out.replace(f"{{{{{k}}}}}", v)
    if "{{" in out and "}}" in out:
        raise ValueError(f"unresolved placeholders remain in prompt: {out[:200]!r}")
    return out


def _extract_json_object(text: str) -> dict[str, Any]:
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"LLM returned no JSON object: {text[:400]!r}")
    blob = text[start : end + 1]
    try:
        return json.loads(blob)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM returned non-JSON payload: {text[:400]!r}") from exc


class LlmClient:
    def __init__(self) -> None:
        settings = get_settings()
        key = settings.gemini_api_key.strip()
        if not key:
            raise RuntimeError("GEMINI_API_KEY is not configured (or set GOOGLE_API_KEY)")
        self._client = genai.Client(api_key=key)
        self._model_name = settings.gemini_model.strip()

    def complete_json(
        self,
        *,
        system: str,
        user: str,
        prompt_version: str,
        max_tokens: int = 4096,
    ) -> tuple[dict[str, Any], dict[str, int]]:
        """
        Returns parsed JSON object + usage dict {input_tokens, output_tokens}.
        """
        attempt = 0
        last_exc: Exception | None = None
        while attempt < _MAX_RETRIES:
            attempt += 1
            try:
                response = self._client.models.generate_content(
                    model=self._model_name,
                    contents=user,
                    config=types.GenerateContentConfig(
                        system_instruction=system,
                        max_output_tokens=max_tokens,
                        response_mime_type="application/json",
                    ),
                )
                if not response.candidates:
                    fb = getattr(response, "prompt_feedback", None)
                    raise ValueError(f"Gemini returned no candidates (blocked or empty): {fb!r}")

                text = (response.text or "").strip()
                if not text:
                    raise ValueError("Gemini returned empty text")
                data = _extract_json_object(text)
                um = getattr(response, "usage_metadata", None)
                usage_in = int(getattr(um, "prompt_token_count", 0) or 0) if um else 0
                usage_out = int(getattr(um, "candidates_token_count", 0) or 0) if um else 0
                _LOG.info(
                    "llm.complete_json",
                    extra={
                        "prompt_version": prompt_version,
                        "input_tokens": usage_in,
                        "output_tokens": usage_out,
                        "model": self._model_name,
                    },
                )
                return data, {"input_tokens": usage_in, "output_tokens": usage_out}
            except genai_errors.APIError as exc:
                last_exc = exc
                if not _is_retryable_api_error(exc) or attempt >= _MAX_RETRIES:
                    break
                sleep_s = _BACKOFF_BASE_S * (2 ** (attempt - 1))
                _LOG.warning(
                    "llm.retry",
                    extra={"attempt": attempt, "sleep_s": sleep_s, "error": repr(exc)},
                )
                time.sleep(sleep_s)
            except (json.JSONDecodeError, ValueError, AttributeError) as exc:
                last_exc = exc
                if attempt >= _MAX_RETRIES:
                    break
                sleep_s = _BACKOFF_BASE_S * (2 ** (attempt - 1))
                _LOG.warning(
                    "llm.retry_json",
                    extra={"attempt": attempt, "sleep_s": sleep_s, "error": repr(exc)},
                )
                time.sleep(sleep_s)
        assert last_exc is not None
        raise last_exc
