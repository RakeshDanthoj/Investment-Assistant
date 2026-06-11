"""OpenAI-compatible LLM client (NVIDIA Nemotron via integrate API) with retries (P1-S7)."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI, RateLimitError

from app.core.settings import get_settings

_LOG = logging.getLogger(__name__)

_REPO_PROMPTS = Path(__file__).resolve().parents[2] / "prompts"
_MAX_RETRIES = 4
_BACKOFF_BASE_S = 0.7
_DEFAULT_BASE_URL = "https://integrate.api.nvidia.com/v1"


def _is_retryable_api_error(exc: BaseException) -> bool:
    if isinstance(exc, (APIConnectionError, APITimeoutError, RateLimitError)):
        return True
    return isinstance(exc, APIStatusError) and exc.status_code in {
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


def _message_text(message: Any) -> str:
    parts: list[str] = []
    for attr in ("content", "reasoning", "reasoning_content"):
        val = getattr(message, attr, None)
        if isinstance(val, str) and val.strip():
            parts.append(val.strip())
    return "\n".join(parts)


class LlmClient:
    def __init__(self) -> None:
        settings = get_settings()
        key = settings.nvidia_api_key.strip()
        if not key:
            raise RuntimeError("NVIDIA_API_KEY is not configured")
        base_url = settings.llm_base_url.strip() or _DEFAULT_BASE_URL
        self._client = OpenAI(api_key=key, base_url=base_url)
        self._model_name = settings.llm_model.strip()

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
                response = self._client.chat.completions.create(
                    model=self._model_name,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    max_tokens=max_tokens,
                    temperature=0.2,
                    response_format={"type": "json_object"},
                )
                if not response.choices:
                    raise ValueError("LLM returned no choices (blocked or empty)")

                text = _message_text(response.choices[0].message)
                if not text:
                    raise ValueError("LLM returned empty text")
                data = _extract_json_object(text)
                usage = response.usage
                usage_in = int(usage.prompt_tokens or 0) if usage else 0
                usage_out = int(usage.completion_tokens or 0) if usage else 0
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
            except (APIConnectionError, APITimeoutError, RateLimitError, APIStatusError) as exc:
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
