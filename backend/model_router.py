"""The sole external-model touchpoint for PakkaHisaab.

Two providers live here and nowhere else:

* **OpenAI** — vision, classification, reasoning, drafting, Whisper, TTS. Reachable either
  directly (`OPENAI_API_KEY`) or through **Azure OpenAI** (`AZURE_OPENAI_*`), which routes
  by *deployment name* rather than model id and requires `max_completion_tokens`. Azure
  serves `chat`-modality tasks only: a text deployment cannot transcribe audio, and sending
  it audio would fail confusingly rather than loudly.
* **Sarvam AI** — `saaras:v3` speech-to-text and `bulbul:v3` speech synthesis for Indic
  audio. Saaras is an Indian sovereign model built for code-mixed Hindi/English speech,
  and its `transcribe` mode normalizes spoken numbers to digits ("पच्चीस सौ" → 2500),
  which is precisely what our amount extraction needs. Request shapes were read from
  docs.sarvam.ai on 2026-07-29 before implementation.

Every Indic task has an explicit OpenAI fallback and both legs are logged, so the eval
page can state which provider actually served a request rather than which one we hoped
would.
"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging
import os
import re
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Awaitable, Callable

import httpx

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RouteConfig:
    model: str
    max_tokens: int | None
    provider: str = "openai"
    # `chat` tasks can be served by Azure; `transcription`/`speech` need the provider's
    # dedicated audio endpoints and must never be sent to a chat deployment.
    modality: str = "chat"


ROUTING_TABLE: dict[str, RouteConfig] = {
    "vision_khaata": RouteConfig("gpt-4o", 2000),
    "vision_invoice": RouteConfig("gpt-4o", 1500),
    "vision_upi_screenshot": RouteConfig("gpt-4o-mini", 500),
    "transcribe_indic": RouteConfig("saaras:v3", None, provider="sarvam", modality="transcription"),
    "transcribe_hi": RouteConfig("whisper-1", None, modality="transcription"),
    "classify_txn": RouteConfig("gpt-4o-mini", 200),
    "exception_reasoning": RouteConfig("gpt-4o", 1200),
    "notice_draft": RouteConfig("gpt-4o", 2500),
    "nl_query": RouteConfig("gpt-4o-mini", 800),
    "tts_indic": RouteConfig("bulbul:v3", None, provider="sarvam", modality="speech"),
    "tts_hi": RouteConfig("tts-1", None, modality="speech"),
}

# Indic-first, OpenAI as the safety net. Both legs are recorded in `model_calls`.
FALLBACK_CHAIN = {"transcribe_indic": "transcribe_hi", "tts_indic": "tts_hi"}

FIXTURE_BY_TASK = {
    "vision_khaata": "vision_khaata.json",
    "vision_invoice": "vision_invoice.json",
    "transcribe_indic": "transcribe_indic.json",
    "transcribe_hi": "transcribe_hi.json",
    "classify_txn": "classify_txn.json",
    "tts_indic": "tts_indic.json",
    "tts_hi": "tts_hi.json",
}
FIXTURES_DIR = Path(__file__).resolve().parents[1] / "sample_data" / "fixtures"
PRICE_PER_MILLION = {"gpt-4o": (2.50, 10.00), "gpt-4o-mini": (0.15, 0.60)}

AZURE_PROVIDER = "azure_openai"
OPENAI_PROVIDER = "openai"
# Azure pins the wire format by date. This default is the current GA version; override with
# AZURE_OPENAI_API_VERSION if the resource is pinned elsewhere.
AZURE_DEFAULT_API_VERSION = "2024-10-21"

SARVAM_BASE_URL = "https://api.sarvam.ai"
SARVAM_STT_PATH = "/speech-to-text"
SARVAM_TTS_PATH = "/text-to-speech"
SARVAM_LANGUAGE = "hi-IN"
# Sarvam publishes speech-to-text at ₹30 per hour of audio. Costs are stored in INR and
# labelled as such; converting to USD at an invented FX rate would be a fabricated number.
SARVAM_STT_INR_PER_HOUR = 30.0
DEFAULT_MOCK_AUDIO_SECONDS = 6


def sarvam_stt_cost_inr(audio_seconds: float) -> float:
    """Cost in rupees for `audio_seconds` of Saaras transcription."""
    if audio_seconds <= 0:
        return 0.0
    return SARVAM_STT_INR_PER_HOUR * audio_seconds / 3600


class RouterError(RuntimeError):
    """A caller-visible, safe failure after router retries are exhausted."""


@dataclass(frozen=True)
class ModelCall:
    task: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: int
    success: bool
    provider: str = "openai"
    cost_inr: float = 0.0
    currency: str = "USD"
    fallback_from: str | None = None
    # True when a committed fixture answered instead of the vendor. `provider` still names
    # the vendor that owns the task, so cost currency and the eval page stay correct, while
    # this flag keeps the telemetry from implying a call that never left the process.
    from_fixture: bool = False
    # False when no published price exists for `model` (e.g. a custom Azure deployment).
    # The token counts are still real; only the money is unknown.
    cost_known: bool = True


@dataclass(frozen=True)
class Provenance:
    """Which provider actually served a request, and what it fell back from."""

    task: str
    model: str
    provider: str
    fell_back_from: str | None = None


MODEL_CALLS: list[ModelCall] = []


def parse_json_object(content: str) -> dict[str, Any]:
    stripped = content.strip()
    stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
    stripped = re.sub(r"\s*```$", "", stripped).strip()
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError as exc:
        raise RouterError("Model did not return a valid JSON object") from exc
    if not isinstance(parsed, dict):
        raise RouterError("Model response must be a JSON object")
    return parsed


def read_usage(usage: object) -> tuple[int, int]:
    """Token counts from either shape of usage payload.

    The OpenAI SDK returns an object with attributes; Azure's REST response returns a plain
    JSON dict. Reading only attributes silently recorded zero tokens — and therefore zero
    cost — for every Azure call.
    """
    if usage is None:
        return 0, 0
    if isinstance(usage, dict):
        return int(usage.get("prompt_tokens") or 0), int(usage.get("completion_tokens") or 0)
    return int(getattr(usage, "prompt_tokens", 0) or 0), int(getattr(usage, "completion_tokens", 0) or 0)


def _cost(model: str, input_tokens: int, output_tokens: int) -> float:
    prices = PRICE_PER_MILLION.get(model, (0.0, 0.0))
    return (input_tokens * prices[0] + output_tokens * prices[1]) / 1_000_000


def is_priced(model: str) -> bool:
    """Whether we hold a published price for this model.

    Azure deployments carry arbitrary names and their rates are per-agreement, so a
    deployment we have no price for records its real token counts and `cost_known=False`.
    Reporting $0.00 for a call that cost money would be a fabricated figure, which is
    exactly what this project refuses to do elsewhere.
    """
    return model in PRICE_PER_MILLION


async def _persist_model_call(call: ModelCall) -> None:
    """Best-effort service-role persistence; memory telemetry remains test-safe."""
    supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
    service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    if not supabase_url or not service_role_key:
        return
    payload = {
        "task": call.task,
        "model": call.model,
        "input_tokens": call.input_tokens,
        "output_tokens": call.output_tokens,
        "cost_usd": call.cost_usd,
        "latency_ms": call.latency_ms,
        "success": call.success,
        "provider": call.provider,
        "cost_inr": call.cost_inr,
        "currency": call.currency,
        "fallback_from": call.fallback_from,
        "from_fixture": call.from_fixture,
        "cost_known": call.cost_known,
    }
    for _attempt in range(2):
        try:
            async with httpx.AsyncClient(base_url=supabase_url, timeout=5.0) as client:
                response = await client.post(
                    "/rest/v1/model_calls",
                    headers={
                        "apikey": service_role_key,
                        "Authorization": f"Bearer {service_role_key}",
                        "Prefer": "return=minimal",
                    },
                    json=payload,
                )
                response.raise_for_status()
                return
        except httpx.HTTPError:
            continue
    # Operational telemetry must never make the intake result unavailable.


async def _record(
    task: str,
    config: RouteConfig,
    started: float,
    success: bool,
    input_tokens: int = 0,
    output_tokens: int = 0,
    *,
    audio_seconds: float = 0.0,
    fallback_from: str | None = None,
    from_fixture: bool = False,
) -> None:
    sarvam = config.provider == "sarvam"
    call = ModelCall(
        task=task,
        model=config.model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=0.0 if sarvam else _cost(config.model, input_tokens, output_tokens),
        latency_ms=int((time.perf_counter() - started) * 1000),
        success=success,
        provider=config.provider,
        cost_inr=sarvam_stt_cost_inr(audio_seconds) if sarvam and task.startswith("transcribe") else 0.0,
        currency="INR" if sarvam else "USD",
        fallback_from=fallback_from,
        from_fixture=from_fixture,
        cost_known=True if sarvam else is_priced(config.model),
    )
    MODEL_CALLS.append(call)
    await _persist_model_call(call)


def _load_fixture(task: str) -> dict[str, Any]:
    filename = FIXTURE_BY_TASK.get(task)
    if not filename:
        raise RouterError(f"No mock fixture is defined for task '{task}'")
    path = FIXTURES_DIR / filename
    try:
        return parse_json_object(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RouterError(f"Mock fixture is missing for task '{task}'") from exc


def resolve_chat_provider() -> str:
    """Which OpenAI-family provider serves chat tasks right now.

    Azure wins when configured because that is the deliberate deployment choice; direct
    OpenAI is the fallback. Raises rather than returning a provider we have no key for, so
    a misconfiguration surfaces as a typed `RouterError` instead of a 401 mid-demo.
    """
    if os.environ.get("AZURE_OPENAI_API_KEY") and os.environ.get("AZURE_OPENAI_ENDPOINT"):
        return AZURE_PROVIDER
    if os.environ.get("OPENAI_API_KEY"):
        return OPENAI_PROVIDER
    raise RouterError(
        "No chat provider is configured — set AZURE_OPENAI_API_KEY + AZURE_OPENAI_ENDPOINT, "
        "or OPENAI_API_KEY"
    )


def azure_deployment() -> str:
    """The deployment that serves chat tasks. Azure addresses models by deployment name."""
    deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "")
    if not deployment:
        raise RouterError("AZURE_OPENAI_DEPLOYMENT_NAME is not configured")
    return deployment


def build_azure_request(
    config: RouteConfig, payload: dict[str, Any]
) -> tuple[str, dict[str, str], dict[str, Any]]:
    """Build the Azure chat-completions request. Pure, so it is testable without a key.

    Two Azure-specific facts are encoded here. The model is named by the URL's deployment
    segment, not the body. And the token cap is `max_completion_tokens`: reasoning-capable
    deployments reject `max_tokens` with a 400.
    """
    if config.modality != "chat":
        raise RouterError(
            f"Azure OpenAI serves chat tasks only; '{config.modality}' needs a dedicated "
            "audio deployment"
        )
    messages = payload.get("messages")
    if not isinstance(messages, list) or not messages:
        raise RouterError("Azure chat calls require a non-empty messages list")

    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/")
    version = os.environ.get("AZURE_OPENAI_API_VERSION") or AZURE_DEFAULT_API_VERSION
    url = f"{endpoint}/openai/deployments/{azure_deployment()}/chat/completions?api-version={version}"
    headers = {"api-key": os.environ["AZURE_OPENAI_API_KEY"], "content-type": "application/json"}
    body: dict[str, Any] = {"messages": messages, "response_format": {"type": "json_object"}}
    if config.max_tokens is not None:
        body["max_completion_tokens"] = config.max_tokens
    return url, headers, body


async def _azure_request(config: RouteConfig, payload: dict[str, Any]) -> object:
    url, headers, body = build_azure_request(config, payload)
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=headers, json=body)
        response.raise_for_status()
        data = response.json()
    choice = data.get("choices") or [{}]
    return {"content": (choice[0].get("message") or {}).get("content") or "", "usage": data.get("usage")}


def _sarvam_key() -> str:
    key = os.environ.get("SARVAM_API_KEY", "")
    if not key:
        raise RouterError("SARVAM_API_KEY is not configured")
    return key


async def _sarvam_transcribe(config: RouteConfig, payload: dict[str, Any]) -> object:
    """POST multipart audio to Sarvam speech-to-text.

    Field names and the `api-subscription-key` header are the documented contract:
    `file`, `model`, `mode`, `language_code`. `mode="transcribe"` is what performs the
    spoken-number normalization our amount extraction depends on.
    """
    audio = payload.get("audio_bytes")
    if not isinstance(audio, (bytes, bytearray)):
        raise RouterError("transcribe_indic requires audio_bytes")
    files = {"file": (str(payload.get("filename") or "audio.wav"), bytes(audio), "application/octet-stream")}
    data = {
        "model": config.model,
        "mode": str(payload.get("mode") or "transcribe"),
        "language_code": str(payload.get("language_code") or SARVAM_LANGUAGE),
    }
    async with httpx.AsyncClient(base_url=SARVAM_BASE_URL, timeout=30.0) as client:
        response = await client.post(
            SARVAM_STT_PATH, headers={"api-subscription-key": _sarvam_key()}, data=data, files=files
        )
        response.raise_for_status()
        return response.json()


async def _sarvam_tts(config: RouteConfig, payload: dict[str, Any]) -> object:
    """POST JSON to Sarvam text-to-speech; the reply carries base64 audio in `audios`."""
    text = payload.get("text")
    if not isinstance(text, str) or not text.strip():
        raise RouterError("tts_indic requires text")
    body = {
        "text": text,
        "target_language_code": str(payload.get("target_language_code") or SARVAM_LANGUAGE),
        "model": config.model,
        "speaker": str(payload.get("speaker") or "shubh"),
    }
    async with httpx.AsyncClient(base_url=SARVAM_BASE_URL, timeout=30.0) as client:
        response = await client.post(
            SARVAM_TTS_PATH, headers={"api-subscription-key": _sarvam_key()}, json=body
        )
        response.raise_for_status()
        return response.json()


SARVAM_REQUEST_BY_TASK = {"transcribe_indic": _sarvam_transcribe, "tts_indic": _sarvam_tts}


def effective_config(task: str, config: RouteConfig) -> RouteConfig:
    """Resolve the config actually used, so telemetry names the real provider and model.

    An OpenAI-family chat task served through Azure is recorded as `azure_openai` with the
    deployment as its model — anything else would put a model id in `model_calls` that was
    never actually invoked.
    """
    if config.provider != OPENAI_PROVIDER or config.modality != "chat":
        return config
    try:
        if resolve_chat_provider() != AZURE_PROVIDER:
            return config
        return replace(config, provider=AZURE_PROVIDER, model=azure_deployment())
    except RouterError:
        # No usable credentials. Keep the declared config so a caller supplying its own
        # request function still works, and let the actual call surface the real failure.
        return config


async def _openai_request(config: RouteConfig, payload: dict[str, Any]) -> object:
    # This is deliberately the only OpenAI import in the repository.
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    messages = payload.get("messages")
    if not isinstance(messages, list):
        raise RouterError("Non-mock calls require OpenAI chat messages")
    response = await client.chat.completions.create(
        model=config.model,
        messages=messages,
        max_tokens=config.max_tokens,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or ""
    return {"content": content, "usage": response.usage}


async def route(
    task: str, payload: dict[str, Any], *, mock_mode: bool | None = None, fallback_from: str | None = None
) -> dict[str, Any]:
    """Route one task, retry once, and record operational telemetry for every call."""
    if task not in ROUTING_TABLE:
        raise RouterError(f"Unknown model task '{task}'")
    config = ROUTING_TABLE[task]
    started = time.perf_counter()
    use_mock = (os.getenv("MOCK_MODE", "false").lower() == "true") if mock_mode is None else mock_mode
    audio_seconds = float(payload.get("audio_seconds") or 0.0)
    if use_mock:
        try:
            result = _load_fixture(task)
        except RouterError:
            await _record(
                task, config, started, False, audio_seconds=audio_seconds,
                fallback_from=fallback_from, from_fixture=True,
            )
            raise
        if config.provider == "sarvam" and audio_seconds == 0.0:
            audio_seconds = DEFAULT_MOCK_AUDIO_SECONDS
        await _record(
            task, config, started, True, audio_seconds=audio_seconds,
            fallback_from=fallback_from, from_fixture=True,
        )
        return result

    config = effective_config(task, config)
    request = payload.get("request")
    if task in SARVAM_REQUEST_BY_TASK:
        default_request = SARVAM_REQUEST_BY_TASK[task]
    elif config.provider == AZURE_PROVIDER:
        default_request = _azure_request
    else:
        default_request = _openai_request
    request_fn: Callable[[dict[str, Any]], Awaitable[object]] = (
        request if callable(request) else lambda data: default_request(config, data)
    )
    last_error: Exception | None = None
    for _attempt in range(2):
        try:
            response = await asyncio.wait_for(request_fn(payload), timeout=30)
            if inspect.isawaitable(response):
                response = await response
            if isinstance(response, dict) and "content" in response:
                result = parse_json_object(str(response["content"]))
                input_tokens, output_tokens = read_usage(response.get("usage"))
            elif isinstance(response, dict):
                result = response
                input_tokens = output_tokens = 0
            else:
                raise RouterError("Unsupported model response")
            await _record(
                task, config, started, True, input_tokens, output_tokens,
                audio_seconds=audio_seconds, fallback_from=fallback_from,
            )
            return result
        except Exception as exc:  # RouterError is also retried once for transient provider glitches.
            last_error = exc
    await _record(task, config, started, False, audio_seconds=audio_seconds, fallback_from=fallback_from)
    raise RouterError(f"Task '{task}' failed after 2 attempts") from last_error


async def route_with_fallback(
    task: str,
    payload: dict[str, Any],
    *,
    fallback_payload: dict[str, Any] | None = None,
    mock_mode: bool | None = None,
) -> tuple[dict[str, Any], Provenance]:
    """Run an Indic task, falling back to its OpenAI equivalent on `RouterError`.

    Returns the result together with a `Provenance` naming the provider that actually
    answered, so callers and the eval page never have to guess. Both the failed primary
    and the successful fallback are recorded in `model_calls`.
    """
    try:
        result = await route(task, payload, mock_mode=mock_mode)
        config = ROUTING_TABLE[task]
        return result, Provenance(task, config.model, config.provider)
    except RouterError as primary_error:
        fallback = FALLBACK_CHAIN.get(task)
        if not fallback:
            raise
        logger.warning("Task '%s' failed (%s); falling back to '%s'", task, primary_error, fallback)
        result = await route(
            fallback, fallback_payload if fallback_payload is not None else payload,
            mock_mode=mock_mode, fallback_from=task,
        )
        config = ROUTING_TABLE[fallback]
        return result, Provenance(fallback, config.model, config.provider, fell_back_from=task)
