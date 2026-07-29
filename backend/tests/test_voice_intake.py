"""Voice-note intake: Sarvam-first transcription, then amount extraction."""
from __future__ import annotations

import asyncio

import pytest

from agents.intake_agent import (
    InMemoryExtractionRepository,
    IntakeAgent,
    SourceDocument,
    amount_paise_from_transcript,
    transcript_text,
)


def _agent(events: list[dict[str, object]]) -> tuple[IntakeAgent, InMemoryExtractionRepository]:
    repository = InMemoryExtractionRepository()
    return IntakeAgent(repository=repository, emit=events.append, mock_mode=True), repository


def test_transcript_text_reads_both_provider_shapes() -> None:
    """Sarvam returns `transcript`; Whisper returns `text`. Both are native shapes."""
    assert transcript_text({"transcript": "रमेश को 2500 रुपये"}) == "रमेश को 2500 रुपये"
    assert transcript_text({"text": "रमेश को पच्चीस सौ रुपये"}) == "रमेश को पच्चीस सौ रुपये"
    with pytest.raises(Exception):
        transcript_text({"nothing": 1})


def test_amount_extraction_reads_digits_first_then_falls_back_to_words() -> None:
    """Digits are primary because Saaras usually normalizes them (5/5 live calls on the
    seeded note). Words are the net, because it is not guaranteed — the same sentence with
    different prosody kept `पच्चीस सौ` intact. Either way the number comes from code."""
    assert amount_paise_from_transcript("रमेश को 2500 रुपये कैश दिए") == 250_000
    assert amount_paise_from_transcript("₹4,800 का बिल") == 480_000
    assert amount_paise_from_transcript("2,500.50 रुपये") == 250_050
    # The word-number path: this is the transcript Saaras actually returned once.
    assert amount_paise_from_transcript("रमेश को पच्चीस सौ रुपये कैश दिए") == 250_000
    assert amount_paise_from_transcript("चार हज़ार आठ सौ रुपये") == 480_000
    # Still refuses to invent one when there is no number at all.
    assert amount_paise_from_transcript("रमेश को कैश दिए") is None
    assert amount_paise_from_transcript("") is None


def test_voice_note_intake_produces_one_entry_with_the_normalized_amount() -> None:
    events: list[dict[str, object]] = []
    agent, repository = _agent(events)
    document = SourceDocument("doc-voice", "store-1", "voice_note", "voice_ramesh.m4a")

    entries = asyncio.run(agent.process(document))

    assert len(entries) == 1
    entry = entries[0]
    assert entry.amount_paise == 250_000
    assert entry.party_name == "Ramesh"
    assert entry.entry_type == "payment_out"
    assert "2500" in entry.description
    assert repository.entries == entries


def test_voice_intake_reports_the_serving_provider_on_the_agent_log() -> None:
    events: list[dict[str, object]] = []
    agent, _ = _agent(events)
    asyncio.run(agent.process(SourceDocument("doc-voice", "store-1", "voice_note", "voice_ramesh.m4a")))

    details = [str(event.get("detail") or "") for event in events]
    assert any("sarvam" in detail for detail in details), details
    assert any("saaras:v3" in detail for detail in details), details


def test_voice_note_upload_route_reaches_the_indic_transcription_path() -> None:
    """The multipart route must hand raw audio bytes to the router, not decoded text."""
    from fastapi.testclient import TestClient

    from main import DEMO_STORE_ID, app

    client = TestClient(app)
    response = client.post(
        f"/api/stores/{DEMO_STORE_ID}/uploads",
        data={"kind": "voice_note"},
        files={"file": ("voice_ramesh.m4a", b"\x00\x01\x02\x03", "audio/m4a")},
    )

    assert response.status_code == 200
    assert response.json()["entry_count"] == 1
