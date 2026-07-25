"""The sole OpenAI SDK touchpoint for PakkaHisaab model tasks."""

from __future__ import annotations

import asyncio
import inspect
import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable

import httpx


@dataclass(frozen=True)
class RouteConfig:
    model: str
    max_tokens: int | None


ROUTING_TABLE: dict[str, RouteConfig] = {
    "vision_khaata": RouteConfig("gpt-4o", 2000),
    "vision_invoice": RouteConfig("gpt-4o", 1500),
    "vision_upi_screenshot": RouteConfig("gpt-4o-mini", 500),
    "transcribe_hi": RouteConfig("whisper-1", None),
    "classify_txn": RouteConfig("gpt-4o-mini", 200),
    "exception_reasoning": RouteConfig("gpt-4o", 1200),
    "notice_draft": RouteConfig("gpt-4o", 2500),
    "nl_query": RouteConfig("gpt-4o-mini", 800),
    "tts_hi": RouteConfig("tts-1", None),
}
FIXTURE_BY_TASK = {"vision_khaata": "vision_khaata.json", "vision_invoice": "vision_invoice.json"}
FIXTURES_DIR = Path(__file__).resolve().parents[1] / "sample_data" / "fixtures"
PRICE_PER_MILLION = {"gpt-4o": (2.50, 10.00), "gpt-4o-mini": (0.15, 0.60)}


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


async def _record(task: str, config: RouteConfig, started: float, success: bool, input_tokens: int = 0, output_tokens: int = 0) -> None:
    call = ModelCall(
        task=task,
        model=config.model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=_cost(config.model, input_tokens, output_tokens),
        latency_ms=int((time.perf_counter() - started) * 1000),
        success=success,
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


async def route(task: str, payload: dict[str, Any], *, mock_mode: bool | None = None) -> dict[str, Any]:
    """Route one task, retry once, and record operational telemetry for every call."""
    if task not in ROUTING_TABLE:
        raise RouterError(f"Unknown model task '{task}'")
    config = ROUTING_TABLE[task]
    started = time.perf_counter()
    use_mock = (os.getenv("MOCK_MODE", "false").lower() == "true") if mock_mode is None else mock_mode
    if use_mock:
        try:
            result = _load_fixture(task)
        except RouterError:
            await _record(task, config, started, False)
            raise
        await _record(task, config, started, True)
        return result

    request = payload.get("request")
    request_fn: Callable[[dict[str, Any]], Awaitable[object]] = request if callable(request) else lambda data: _openai_request(config, data)
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
            await _record(task, config, started, True, input_tokens, output_tokens)
            return result
        except Exception as exc:  # RouterError is also retried once for transient provider glitches.
            last_error = exc
    await _record(task, config, started, False)
    raise RouterError(f"Task '{task}' failed after 2 attempts") from last_error
