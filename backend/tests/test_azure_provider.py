"""Azure OpenAI as a provider for chat-modality router tasks.

Every test here is offline: `build_azure_request` is a pure function, so the URL shape,
api-version, auth header, and the `max_tokens` → `max_completion_tokens` substitution are
all verifiable without a network call or a key.
"""
from __future__ import annotations

import asyncio

import pytest

from model_router import (
    MODEL_CALLS,
    ROUTING_TABLE,
    RouterError,
    build_azure_request,
    resolve_chat_provider,
    route,
)

AZURE_ENV = {
    "AZURE_OPENAI_API_KEY": "test-key-not-real",
    "AZURE_OPENAI_ENDPOINT": "https://example-resource.openai.azure.com/",
    "AZURE_OPENAI_DEPLOYMENT_NAME": "gpt-5.4",
    "AZURE_OPENAI_API_VERSION": "2024-10-21",
}


def _use_azure(monkeypatch) -> None:
    for key, value in AZURE_ENV.items():
        monkeypatch.setenv(key, value)


def _no_providers(monkeypatch) -> None:
    for key in (*AZURE_ENV, "OPENAI_API_KEY"):
        monkeypatch.delenv(key, raising=False)


def test_chat_provider_is_azure_when_azure_is_configured(monkeypatch) -> None:
    _use_azure(monkeypatch)
    assert resolve_chat_provider() == "azure_openai"


def test_chat_provider_falls_back_to_openai_without_azure(monkeypatch) -> None:
    _no_providers(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-not-real")
    assert resolve_chat_provider() == "openai"


def test_azure_request_targets_the_deployment_and_carries_api_key_header(monkeypatch) -> None:
    _use_azure(monkeypatch)
    url, headers, body = build_azure_request(
        ROUTING_TABLE["classify_txn"], {"messages": [{"role": "user", "content": "hi"}]}
    )

    # Azure routes by deployment name, not model id — the model never appears in the body.
    assert url.startswith(
        "https://example-resource.openai.azure.com/openai/deployments/gpt-5.4/chat/completions"
    )
    assert "api-version=2024-10-21" in url
    assert headers["api-key"] == AZURE_ENV["AZURE_OPENAI_API_KEY"]
    assert "Authorization" not in headers
    assert "model" not in body


def test_azure_request_uses_max_completion_tokens_not_max_tokens(monkeypatch) -> None:
    """The gpt-5.4 deployment rejects `max_tokens` outright with a 400."""
    _use_azure(monkeypatch)
    _, _, body = build_azure_request(
        ROUTING_TABLE["classify_txn"], {"messages": [{"role": "user", "content": "hi"}]}
    )
    assert "max_tokens" not in body
    assert body["max_completion_tokens"] == ROUTING_TABLE["classify_txn"].max_tokens
    assert body["response_format"] == {"type": "json_object"}


def test_azure_request_omits_the_token_cap_when_the_task_has_none(monkeypatch) -> None:
    _use_azure(monkeypatch)
    _, _, body = build_azure_request(
        ROUTING_TABLE["notice_draft"], {"messages": [{"role": "user", "content": "hi"}]}
    )
    assert body["max_completion_tokens"] == 2500


def test_azure_request_refuses_a_payload_without_messages(monkeypatch) -> None:
    _use_azure(monkeypatch)
    with pytest.raises(RouterError, match="messages"):
        build_azure_request(ROUTING_TABLE["classify_txn"], {"prompt": "wrong shape"})


def test_audio_tasks_are_never_routed_to_the_text_deployment(monkeypatch) -> None:
    """Only `gpt-5.4` is deployed. Sending transcription there would either 404 or, worse,
    return prose that looked like a transcript — so audio modality must refuse Azure."""
    _use_azure(monkeypatch)
    assert ROUTING_TABLE["transcribe_hi"].modality == "transcription"
    assert ROUTING_TABLE["tts_hi"].modality == "speech"
    assert ROUTING_TABLE["classify_txn"].modality == "chat"

    with pytest.raises(RouterError, match="Azure"):
        build_azure_request(ROUTING_TABLE["transcribe_hi"], {"messages": []})


def test_model_calls_record_azure_as_the_serving_provider(monkeypatch) -> None:
    _use_azure(monkeypatch)
    MODEL_CALLS.clear()

    async def azure_answered(_: object) -> object:
        return {"content": '{"entry_type": "payment_out"}', "usage": None}

    asyncio.run(route("classify_txn", {"request": azure_answered}, mock_mode=False))

    call = MODEL_CALLS[-1]
    assert call.provider == "azure_openai"
    assert call.model == "gpt-5.4", "the deployment served the call, so record the deployment"
    assert call.success is True


def test_mock_mode_is_unaffected_by_azure_configuration(monkeypatch) -> None:
    _use_azure(monkeypatch)
    MODEL_CALLS.clear()
    result = asyncio.run(route("vision_khaata", {}, mock_mode=True))
    assert result["entries"]
    call = MODEL_CALLS[-1]
    # A fixture answered, so `from_fixture` says so — but `provider` still names the vendor
    # that owns the task, which is what keeps cost currency correct on the eval page.
    assert call.from_fixture is True
    assert call.provider == "openai"


def test_missing_every_credential_raises_a_typed_error(monkeypatch) -> None:
    _no_providers(monkeypatch)
    with pytest.raises(RouterError, match="No chat provider"):
        resolve_chat_provider()


def test_usage_is_read_from_both_a_dict_and_an_object() -> None:
    """Azure returns usage as JSON; the OpenAI SDK returns an object. Reading only
    attributes recorded 0 tokens and $0.00 for every Azure call."""
    from types import SimpleNamespace

    from model_router import read_usage

    assert read_usage({"prompt_tokens": 54, "completion_tokens": 33}) == (54, 33)
    assert read_usage(SimpleNamespace(prompt_tokens=7, completion_tokens=2)) == (7, 2)
    assert read_usage(None) == (0, 0)
    assert read_usage({}) == (0, 0)


def test_azure_call_records_real_token_counts_and_cost(monkeypatch) -> None:
    _use_azure(monkeypatch)
    MODEL_CALLS.clear()

    async def azure_answered(_: object) -> object:
        return {"content": '{"ok": true}', "usage": {"prompt_tokens": 1000, "completion_tokens": 500}}

    asyncio.run(route("vision_invoice", {"request": azure_answered}, mock_mode=False))
    call = MODEL_CALLS[-1]
    assert (call.input_tokens, call.output_tokens) == (1000, 500)
    # We hold no published price for the `gpt-5.4` deployment, so the money is flagged
    # unknown rather than reported as $0.00 — a real call is not a free call.
    assert call.cost_known is False
    assert call.model == "gpt-5.4"


def test_a_priced_model_still_computes_its_cost(monkeypatch) -> None:
    _no_providers(monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-not-real")
    MODEL_CALLS.clear()

    async def openai_answered(_: object) -> object:
        return {"content": '{"ok": true}', "usage": {"prompt_tokens": 1_000_000, "completion_tokens": 0}}

    asyncio.run(route("vision_invoice", {"request": openai_answered}, mock_mode=False))
    call = MODEL_CALLS[-1]
    assert call.model == "gpt-4o"
    assert call.cost_known is True
    assert call.cost_usd == 2.50
