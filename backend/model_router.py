"""The sole external-model touchpoint for PakkaHisaab.

Two providers live here and nowhere else:

* **OpenAI** — vision, classification, reasoning, drafting, Whisper, TTS.
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
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable

import httpx

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RouteConfig:
    model: str
    max_tokens: int | None
    provider: str = "openai"


ROUTING_TABLE: dict[str, RouteConfig] = {
    "vision_khaata": RouteConfig("gpt-4o", 2000),
    "vision_invoice": RouteConfig("gpt-4o", 1500),
    "vision_upi_screenshot": RouteConfig("gpt-4o-mini", 500),
    "transcribe_indic": RouteConfig("saaras:v3", None, provider="sarvam"),
    "transcribe_hi": RouteConfig("whisper-1", None),
    "classify_txn": RouteConfig("gpt-4o-mini", 200),
    "exception_reasoning": RouteConfig("gpt-4o", 1200),
    "notice_draft": RouteConfig("gpt-4o", 2500),
    "nl_query": RouteConfig("gpt-4o-mini", 800),
    "tts_indic": RouteConfig("bulbul:v3", None, provider="sarvam"),
    "tts_hi": RouteConfig("tts-1", None),
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


def _cost(model: str, input_tokens: int, output_tokens: int) -> float:
    prices = PRICE_PER_MILLION.get(model, (0.0, 0.0))
    return (input_tokens * prices[0] + output_tokens * prices[1]) / 1_000_000


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
            await _record(task, config, started, False, audio_seconds=audio_seconds, fallback_from=fallback_from)
            raise
        if config.provider == "sarvam" and audio_seconds == 0.0:
            audio_seconds = DEFAULT_MOCK_AUDIO_SECONDS
        await _record(task, config, started, True, audio_seconds=audio_seconds, fallback_from=fallback_from)
        return result

    request = payload.get("request")
    default_request = SARVAM_REQUEST_BY_TASK.get(task, _openai_request)
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
                usage = response.get("usage")
                input_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
                output_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
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
