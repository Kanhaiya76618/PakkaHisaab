from __future__ import annotations

import asyncio

import pytest

from agents.intake_agent import InMemoryExtractionRepository, IntakeAgent, SourceDocument, websocket_emitter
from events import agent_log_hub
from model_router import RouterError


def test_csv_intake_writes_demo_entries_and_emits_bilingual_progress() -> None:
    events: list[dict[str, str | None]] = []
    repository = InMemoryExtractionRepository()
    agent = IntakeAgent(repository=repository, emit=events.append, mock_mode=True)
    document = SourceDocument(
        id="demo-upi-csv",
        store_id="00000000-0000-0000-0000-000000000001",
        kind="upi_csv",
        filename="july.csv",
        content="Txn Date,Merchant,Amount,UPI Ref\n2026-07-12,Gupta Traders,-4800.00,617234889912\n",
    )

    entries = asyncio.run(agent.process(document))

    assert repository.entries == entries
    assert entries[0].amount_paise == 480000
    assert entries[0].source_document_id == document.id
    assert entries[0].confidence == 1.0
    assert any(event["message_en"] and event["message_hi"] for event in events)


def test_khaata_mock_intake_preserves_row_reference_and_integer_paise() -> None:
    repository = InMemoryExtractionRepository()
    agent = IntakeAgent(repository=repository, emit=lambda _: None, mock_mode=True)
    document = SourceDocument(
        id="demo-khaata-image",
        store_id="00000000-0000-0000-0000-000000000001",
        kind="khaata_photo",
        filename="khaata_page_1.jpg",
    )

    entries = asyncio.run(agent.process(document))

    assert entries
    assert all(isinstance(entry.amount_paise, int) or entry.amount_paise is None for entry in entries)
    assert all(entry.bbox_or_line_ref for entry in entries)
    assert all(entry.extraction_model == "gpt-4o" for entry in entries)


def test_invoice_mock_intake_uses_invoice_route() -> None:
    repository = InMemoryExtractionRepository()
    events: list[dict[str, str | None]] = []
    agent = IntakeAgent(repository=repository, emit=events.append, mock_mode=True)
    document = SourceDocument(
        id="demo-invoice-image",
        store_id="00000000-0000-0000-0000-000000000001",
        kind="invoice_image",
        filename="gupta_inv_231.jpg",
    )

    entries = asyncio.run(agent.process(document))

    assert entries[0].source_document_id == document.id
    assert any("invoice" in (event["message_en"] or "").lower() for event in events)


def test_websocket_emitter_adapts_bilingual_intake_event(monkeypatch) -> None:
    published: list[tuple[str, object]] = []

    async def capture(store_id: str, event: object) -> None:
        published.append((store_id, event))

    monkeypatch.setattr(agent_log_hub, "publish", capture)

    asyncio.run(
        websocket_emitter("demo-store")(
            {"agent": "Intake", "level": "info", "message_en": "Reading", "message_hi": "पढ़ा जा रहा है", "detail": "upi_csv"}
        )
    )

    assert published[0][0] == "demo-store"
    assert published[0][1].message_hi == "पढ़ा जा रहा है"


def test_unsupported_intake_kind_is_not_misrouted_to_invoice() -> None:
    agent = IntakeAgent(repository=InMemoryExtractionRepository(), emit=lambda _: None, mock_mode=True)
    document = SourceDocument(id="voice-1", store_id="demo-store", kind="voice_note", filename="note.m4a")

    with pytest.raises(RouterError, match="Unsupported intake document kind"):
        asyncio.run(agent.process(document))
