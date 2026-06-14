"""LLM client timeout and retry policy."""

from unittest.mock import MagicMock, patch

import pytest
from openai import APITimeoutError

from app.services.llm_client import (
    LlmClient,
    LlmTimeoutError,
    _json_message_text,
)


def test_json_message_text_uses_content_only_when_reasoning_present() -> None:
    message = MagicMock(
        content='{"title": "ok"}',
        reasoning="chain-of-thought should not be merged",
        reasoning_content=None,
    )
    assert _json_message_text(message) == '{"title": "ok"}'


def test_complete_json_maps_api_timeout_to_llm_timeout_error() -> None:
    client = LlmClient.__new__(LlmClient)
    client._timeout_seconds = 90.0
    client._max_retries = 2
    client._model_name = "test-model"

    mock_create = MagicMock(side_effect=APITimeoutError(MagicMock()))
    client._client = MagicMock()
    client._client.chat.completions.create = mock_create

    with pytest.raises(LlmTimeoutError) as exc_info:
        client.complete_json(
            system="sys",
            user="user",
            prompt_version="test.v1",
        )

    assert exc_info.value.timeout_seconds == 90.0
    assert mock_create.call_count == 1


@patch("app.services.llm_client.get_settings")
def test_complete_json_stops_after_configured_max_retries(mock_get_settings) -> None:
    settings = MagicMock()
    settings.nvidia_api_key = "nvapi-test"
    settings.llm_base_url = "https://integrate.api.nvidia.com/v1"
    settings.llm_model = "test-model"
    settings.llm_request_timeout_seconds = 90.0
    settings.llm_max_retries = 2
    mock_get_settings.return_value = settings

    client = LlmClient.__new__(LlmClient)
    client._timeout_seconds = 90.0
    client._max_retries = 2
    client._model_name = "test-model"

    mock_create = MagicMock(
        return_value=MagicMock(
            choices=[MagicMock(message=MagicMock(content="not json at all", reasoning=None))],
            usage=MagicMock(prompt_tokens=1, completion_tokens=1),
        )
    )
    client._client = MagicMock()
    client._client.chat.completions.create = mock_create

    with pytest.raises(ValueError, match="no JSON object"):
        client.complete_json(system="sys", user="user", prompt_version="test.v1")

    assert mock_create.call_count == 2


@patch("app.services.llm_client.get_settings")
def test_openai_client_uses_configured_timeout_and_disables_sdk_retries(
    mock_get_settings,
) -> None:
    settings = MagicMock()
    settings.nvidia_api_key = "nvapi-test"
    settings.llm_base_url = "https://integrate.api.nvidia.com/v1"
    settings.llm_model = "nvidia/nemotron-3-super-120b-a12b"
    settings.llm_request_timeout_seconds = 75.0
    settings.llm_max_retries = 2
    mock_get_settings.return_value = settings

    with patch("app.services.llm_client.OpenAI") as mock_openai:
        LlmClient()

    mock_openai.assert_called_once_with(
        api_key="nvapi-test",
        base_url="https://integrate.api.nvidia.com/v1",
        timeout=75.0,
        max_retries=0,
    )


@patch("app.services.llm_client.get_settings")
def test_complete_json_retries_with_higher_max_tokens_on_truncation(mock_get_settings) -> None:
    settings = MagicMock()
    settings.nvidia_api_key = "nvapi-test"
    settings.llm_base_url = "https://integrate.api.nvidia.com/v1"
    settings.llm_model = "test-model"
    settings.llm_request_timeout_seconds = 90.0
    settings.llm_max_retries = 2
    mock_get_settings.return_value = settings

    truncated = '{\n "title": "RBI Holds Rates",\n "context_layer": "partial'
    full_json = '{"title": "RBI Holds Rates", "context_layer": "done"}'

    client = LlmClient.__new__(LlmClient)
    client._timeout_seconds = 90.0
    client._max_retries = 2
    client._model_name = "test-model"

    mock_create = MagicMock(
        side_effect=[
            MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(content=truncated, reasoning=None),
                        finish_reason="length",
                    )
                ],
                usage=MagicMock(prompt_tokens=100, completion_tokens=4096),
            ),
            MagicMock(
                choices=[
                    MagicMock(
                        message=MagicMock(content=full_json, reasoning=None),
                        finish_reason="stop",
                    )
                ],
                usage=MagicMock(prompt_tokens=100, completion_tokens=200),
            ),
        ]
    )
    client._client = MagicMock()
    client._client.chat.completions.create = mock_create

    data, usage = client.complete_json(
        system="sys",
        user="user",
        prompt_version="synthesis.v1",
        max_tokens=4096,
    )

    assert data["title"] == "RBI Holds Rates"
    assert usage["output_tokens"] == 200
    assert mock_create.call_count == 2
    assert mock_create.call_args_list[0].kwargs["max_tokens"] == 4096
    assert mock_create.call_args_list[1].kwargs["max_tokens"] == 8192


@patch("app.services.llm_client.get_settings")
def test_complete_json_disables_nemotron_thinking_for_structured_output(
    mock_get_settings,
) -> None:
    settings = MagicMock()
    settings.nvidia_api_key = "nvapi-test"
    settings.llm_base_url = "https://integrate.api.nvidia.com/v1"
    settings.llm_model = "nvidia/nemotron-3-super-120b-a12b"
    settings.llm_request_timeout_seconds = 90.0
    settings.llm_max_retries = 1
    mock_get_settings.return_value = settings

    client = LlmClient.__new__(LlmClient)
    client._timeout_seconds = 90.0
    client._max_retries = 1
    client._model_name = "nvidia/nemotron-3-super-120b-a12b"

    mock_create = MagicMock(
        return_value=MagicMock(
            choices=[
                MagicMock(
                    message=MagicMock(content='{"ok": true}', reasoning=None),
                    finish_reason="stop",
                )
            ],
            usage=MagicMock(prompt_tokens=1, completion_tokens=1),
        )
    )
    client._client = MagicMock()
    client._client.chat.completions.create = mock_create

    data, _ = client.complete_json(system="sys", user="user", prompt_version="test.v1")

    assert data == {"ok": True}
    assert mock_create.call_args.kwargs["extra_body"] == {
        "chat_template_kwargs": {"enable_thinking": False},
    }
