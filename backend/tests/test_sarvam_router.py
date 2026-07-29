"""Sarvam Indic speech routing, fallback chain, and cost labelling."""
from __future__ import annotations

import asyncio

import pytest

from model_router import (
    MODEL_CALLS,
    ROUTING_TABLE,
    RouterError,
    route,
    route_with_fallback,
    sarvam_stt_cost_inr,
)


def test_indic_tasks_are_registered_with_the_documented_sarvam_models() -> None:
    assert ROUTING_TABLE["transcribe_indic"].model == "saaras:v3"
    assert ROUTING_TABLE["transcribe_indic"].provider == "sarvam"
    assert ROUTING_TABLE["tts_indic"].model == "bulbul:v3"
    assert ROUTING_TABLE["tts_indic"].provider == "sarvam"
    # The OpenAI fallbacks must remain routable.
    assert ROUTING_TABLE["transcribe_hi"].provider == "openai"
    assert ROUTING_TABLE["tts_hi"].provider == "openai"


def test_mock_mode_returns_the_committed_indic_fixtures_unchanged() -> None:
    result = asyncio.run(route("transcribe_indic", {}, mock_mode=True))
    assert result["transcript"]
    assert result["language_code"] == "hi-IN"


def test_fallback_records_which_provider_actually_served_the_request() -> None:
    MODEL_CALLS.clear()

    async def sarvam_is_down(_: object) -> object:
        raise TimeoutError("sarvam unreachable")

    async def whisper_answers(_: object) -> object:
        return {"transcript": "Ramesh ko 2500 rupaye cash diye", "language_code": "hi-IN"}

    result, provenance = asyncio.run(
        route_with_fallback(
            "transcribe_indic",
            {"request": sarvam_is_down},
            fallback_payload={"request": whisper_answers},
            mock_mode=False,
        )
    )

    assert result["transcript"].startswith("Ramesh")
    assert provenance.task == "transcribe_hi"
    assert provenance.provider == "openai"
    assert provenance.fell_back_from == "transcribe_indic"
    # Both the failed primary and the successful fallback are in the telemetry.
    assert [call.task for call in MODEL_CALLS] == ["transcribe_indic", "transcribe_hi"]
    assert MODEL_CALLS[0].success is False
    assert MODEL_CALLS[0].provider == "sarvam"
    assert MODEL_CALLS[1].success is True
    assert MODEL_CALLS[1].fallback_from == "transcribe_indic"


def test_primary_success_does_not_touch_the_fallback() -> None:
    MODEL_CALLS.clear()
    calls: list[str] = []

    async def sarvam_answers(_: object) -> object:
        calls.append("sarvam")
        return {"transcript": "9840 रुपये", "language_code": "hi-IN"}

    async def whisper(_: object) -> object:
        calls.append("whisper")
        return {"transcript": "should not be used", "language_code": "hi-IN"}

    _, provenance = asyncio.run(
        route_with_fallback(
            "transcribe_indic",
            {"request": sarvam_answers},
            fallback_payload={"request": whisper},
            mock_mode=False,
        )
    )
    assert calls == ["sarvam"]
    assert provenance.provider == "sarvam"
    assert provenance.fell_back_from is None


def test_both_providers_failing_raises_a_typed_router_error() -> None:
    async def dead(_: object) -> object:
        raise TimeoutError("down")

    with pytest.raises(RouterError):
        asyncio.run(
            route_with_fallback(
                "transcribe_indic", {"request": dead}, fallback_payload={"request": dead}, mock_mode=False
            )
        )


def test_sarvam_cost_is_recorded_in_rupees_at_the_published_hourly_rate() -> None:
    # ₹30 per hour of audio.
    assert sarvam_stt_cost_inr(3600) == pytest.approx(30.0)
    assert sarvam_stt_cost_inr(60) == pytest.approx(0.5)
    assert sarvam_stt_cost_inr(0) == 0.0


def test_indic_model_calls_carry_inr_currency_and_zero_usd() -> None:
    MODEL_CALLS.clear()
    asyncio.run(route("transcribe_indic", {"audio_seconds": 6}, mock_mode=True))
    call = MODEL_CALLS[-1]
    assert call.provider == "sarvam"
    assert call.currency == "INR"
    assert call.cost_usd == 0.0
    assert call.cost_inr > 0.0
