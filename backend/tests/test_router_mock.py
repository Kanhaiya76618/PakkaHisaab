from __future__ import annotations

import asyncio

import pytest

from model_router import MODEL_CALLS, ROUTING_TABLE, RouterError, parse_json_object, route


def test_routing_table_covers_day_two_vision_tasks() -> None:
    assert ROUTING_TABLE["vision_khaata"].model == "gpt-4o"
    assert ROUTING_TABLE["vision_invoice"].max_tokens == 1500


def test_mock_router_loads_placeholder_fixture() -> None:
    MODEL_CALLS.clear()
    result = asyncio.run(route("vision_khaata", {"source_document_id": "khaata-1"}, mock_mode=True))

    assert result["entries"]
    assert result["entries"][0]["row_ref"]
    assert MODEL_CALLS[-1].task == "vision_khaata"
    assert MODEL_CALLS[-1].success is True


def test_each_router_call_is_handed_to_model_call_persistence(monkeypatch) -> None:
    persisted: list[object] = []

    async def capture(call: object) -> None:
        persisted.append(call)

    monkeypatch.setattr("model_router._persist_model_call", capture)

    asyncio.run(route("vision_invoice", {}, mock_mode=True))

    assert persisted[0].task == "vision_invoice"


def test_defensive_json_parser_strips_markdown_fences() -> None:
    assert parse_json_object("```json\n{\"entries\": []}\n```") == {"entries": []}


def test_missing_mock_fixture_raises_typed_router_error(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("model_router.FIXTURES_DIR", tmp_path)

    with pytest.raises(RouterError, match="fixture"):
        asyncio.run(route("vision_invoice", {}, mock_mode=True))


def test_non_mock_failure_retries_once_then_raises() -> None:
    attempts = 0

    async def failing_request(_: object) -> object:
        nonlocal attempts
        attempts += 1
        raise TimeoutError("network down")

    with pytest.raises(RouterError, match="failed after 2 attempts"):
        asyncio.run(route("vision_invoice", {"request": failing_request}, mock_mode=False))

    assert attempts == 2
