"""Vision intake must actually look at the document.

The bug this pins: the intake agent used to send `"Extract khaata_page_1.jpg."` as the only
user message — no image at all. Under `MOCK_MODE` a fixture answered, so every test passed and
the demo looked correct. With a live key the model would have been asked to extract amounts
from a *filename*, and it would have invented them into a cashbook.

So there are two rules here, and the second matters more than the first:
  1. When image bytes are present, they are attached as a data URI.
  2. When they are absent, a live call is refused outright rather than sent blind.
"""
from __future__ import annotations

import asyncio
import base64
from pathlib import Path

import pytest

from agents.intake_agent import InMemoryExtractionRepository, IntakeAgent, SourceDocument
from model_router import RouterError

ROOT = Path(__file__).resolve().parents[2]
INVOICE = ROOT / "sample_data" / "mehta_inv_231.jpg"


def _agent(mock_mode: bool, captured: list[dict] | None = None) -> IntakeAgent:
    agent = IntakeAgent(repository=InMemoryExtractionRepository(), emit=lambda _: None, mock_mode=mock_mode)
    if captured is not None:
        agent._captured = captured  # type: ignore[attr-defined]
    return agent


def test_vision_payload_attaches_the_image_as_a_data_uri() -> None:
    from agents.intake_agent import build_vision_messages, INVOICE_SYSTEM_PROMPT

    image = INVOICE.read_bytes()
    messages = build_vision_messages(INVOICE_SYSTEM_PROMPT, "mehta_inv_231.jpg", image, "image/jpeg")

    assert messages[0]["role"] == "system"
    content = messages[1]["content"]
    assert isinstance(content, list), "a vision message must be multipart, not a bare string"

    parts = {part["type"]: part for part in content}
    assert "image_url" in parts, "the image itself must be in the payload"
    url = parts["image_url"]["image_url"]["url"]
    assert url.startswith("data:image/jpeg;base64,")
    assert base64.b64decode(url.split(",", 1)[1]) == image, "the exact bytes must be sent"
    assert "mehta_inv_231.jpg" in parts["text"]["text"]


def test_a_live_vision_call_is_refused_without_the_image() -> None:
    """The core of the bug. Extracting from a filename alone is hallucination, and this is a
    cashbook — refusing is the only safe behaviour."""
    agent = _agent(mock_mode=False)
    document = SourceDocument("d1", "store-1", "invoice_image", "some_invoice.jpg")

    with pytest.raises(RouterError, match="image"):
        asyncio.run(agent.process(document))


def test_mock_mode_still_serves_fixtures_without_an_image() -> None:
    """MOCK_MODE is the documented keyless/offline path: fixtures answer, no model is called,
    so there is nothing to mislead."""
    agent = _agent(mock_mode=True)
    entries = asyncio.run(agent.process(SourceDocument("d1", "store-1", "khaata_photo", "khaata_page_1.jpg")))
    assert entries


def test_uploaded_image_reaches_the_router_with_its_bytes(monkeypatch) -> None:
    seen: dict[str, object] = {}

    async def capture(task, payload, *, mock_mode=None, fallback_from=None):
        seen["task"] = task
        seen["messages"] = payload["messages"]
        return {"entries": [{"entry_type": "purchase", "party_name": "X", "amount_rupees": 10,
                             "entry_date": "2026-07-12", "description": "d",
                             "row_ref": "page 1", "confidence": 1.0}]}

    monkeypatch.setattr("agents.intake_agent.route", capture)
    image = INVOICE.read_bytes()
    agent = _agent(mock_mode=False)
    document = SourceDocument("d1", "store-1", "invoice_image", "mehta_inv_231.jpg",
                              image_bytes=image, media_type="image/jpeg")

    entries = asyncio.run(agent.process(document))

    assert entries[0].amount_paise == 1000
    assert seen["task"] == "vision_invoice"
    content = seen["messages"][1]["content"]
    assert any(part["type"] == "image_url" for part in content)


def test_media_type_follows_the_uploaded_file() -> None:
    from agents.intake_agent import build_vision_messages

    messages = build_vision_messages("sys", "scan.png", b"\x89PNG", "image/png")
    url = messages[1]["content"][1]["image_url"]["url"]
    assert url.startswith("data:image/png;base64,")


def test_upload_route_returns_what_was_read_out_of_the_document() -> None:
    """A judge uploading their own file needs to see the extracted rows, not just a count."""
    from fastapi.testclient import TestClient

    from main import DEMO_STORE_ID, app

    with TestClient(app) as client:
        response = client.post(
            f"/api/stores/{DEMO_STORE_ID}/uploads",
            data={"kind": "upi_csv"},
            files={"file": ("mine.csv",
                            b"Txn Date,Transaction Details,Amount,UPI Ref\n"
                            b"2026-07-12,Gupta Traders,-4800.00,UPI-TEST-1\n", "text/csv")},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["entry_count"] == 1
    entry = body["entries"][0]
    assert entry["amount_paise"] == 480000
    assert entry["amount"] == "₹4,800.00"
    assert entry["party_name"] == "Gupta Traders"


def test_empty_upload_is_rejected_rather_than_reported_as_zero_rows() -> None:
    from fastapi.testclient import TestClient

    from main import DEMO_STORE_ID, app

    with TestClient(app) as client:
        response = client.post(
            f"/api/stores/{DEMO_STORE_ID}/uploads",
            data={"kind": "upi_csv"},
            files={"file": ("empty.csv", b"", "text/csv")},
        )
    assert response.status_code == 422


def test_invoice_line_items_are_notes_so_the_total_is_never_double_counted() -> None:
    """A live call on an unseen invoice returned three line items AND the grand total, all as
    `purchase` — which sums an invoice to nearly double its face value. Line items carry
    detail for the Evidence Passport; only the grand total is a financial entry."""
    from engine.accounting import store_total_paise
    from engine.types import Entry

    from agents.intake_agent import INVOICE_SYSTEM_PROMPT

    prompt = INVOICE_SYSTEM_PROMPT.lower()
    assert "grand total" in prompt or "invoice total" in prompt
    assert "note" in prompt, "the prompt must say how to mark non-total rows"

    # The accounting identity must ignore notes, which is what makes the rule safe.
    entries = [
        Entry("t", "inv", "purchase", "Verma", 1_310_000, "2026-07-18", source_kind="invoice"),
        Entry("l1", "inv", "note", "Verma", 460_000, "2026-07-18", source_kind="invoice"),
        Entry("l2", "inv", "note", "Verma", 640_000, "2026-07-18", source_kind="invoice"),
        Entry("l3", "inv", "note", "Verma", 210_000, "2026-07-18", source_kind="invoice"),
    ]
    assert store_total_paise(entries) == -1_310_000, "notes must not enter the total"


def test_extraction_model_records_the_deployment_that_actually_served(monkeypatch) -> None:
    """Azure substitutes its deployment for the routing table's model id. The Evidence
    Passport shows this string as a badge, so recording `gpt-4o` when `gpt-5.4` ran is a
    provenance lie."""
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "k")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://x.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-5.4")

    async def capture(task, payload, *, mock_mode=None, fallback_from=None):
        return {"entries": [{"entry_type": "purchase", "party_name": "V", "amount_rupees": 100,
                             "entry_date": "2026-07-18", "description": "d",
                             "row_ref": "grand total", "confidence": 1.0}]}

    monkeypatch.setattr("agents.intake_agent.route", capture)
    agent = _agent(mock_mode=False)
    entries = asyncio.run(agent.process(SourceDocument(
        "d", "s", "invoice_image", "x.jpg", image_bytes=b"\xff\xd8\xff", media_type="image/jpeg")))
    assert entries[0].extraction_model == "gpt-5.4"
