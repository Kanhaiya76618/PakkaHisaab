from fastapi.testclient import TestClient

from main import DEMO_STORE_ID, app


client = TestClient(app)


def test_demo_reconcile_runs_engine_and_exposes_live_state() -> None:
    response = client.post(f"/api/stores/{DEMO_STORE_ID}/reconcile")
    assert response.status_code == 200
    assert response.json()["exception_count"] == 4
    assert client.get(f"/api/stores/{DEMO_STORE_ID}/ledger").json()["entries"]
    assert len(client.get(f"/api/stores/{DEMO_STORE_ID}/exceptions").json()["exceptions"]) == 4


def test_exception_resolution_validates_closed_action_set() -> None:
    client.post(f"/api/stores/{DEMO_STORE_ID}/reconcile")
    exception_id = client.get(f"/api/stores/{DEMO_STORE_ID}/exceptions").json()["exceptions"][0]["id"]
    assert client.post(f"/api/exceptions/{exception_id}/resolve", json={"action": "invent"}).status_code == 422
    assert client.post(f"/api/exceptions/{exception_id}/resolve", json={"action": "ask_user"}).status_code == 200


def test_evidence_is_assembled_from_live_reconciliation_state() -> None:
    client.post(f"/api/stores/{DEMO_STORE_ID}/reconcile")
    ledger_entry_id = client.get(f"/api/stores/{DEMO_STORE_ID}/ledger").json()["entries"][0]["id"]
    response = client.get(f"/api/ledger-entries/{ledger_entry_id}/evidence")
    assert response.status_code == 200
    assert response.json()["ledger_entry_id"] == ledger_entry_id
    assert "sources" in response.json()


def test_risk_endpoint_returns_the_seeded_amber_score_after_reconcile() -> None:
    client.post(f"/api/stores/{DEMO_STORE_ID}/reconcile")
    response = client.get(f"/api/stores/{DEMO_STORE_ID}/risk")
    assert response.status_code == 200
    payload = response.json()
    assert payload["risk_score"] == 68
    assert payload["band"] == "watch"
    assert len(payload["gap_by_month"]) == 4
    assert payload["warnings"]
    assert payload["components"]["gap_points"] + payload["components"]["exception_points"] + payload["components"]["personal_points"] == 68


def test_risk_reflects_exceptions_the_user_has_already_resolved() -> None:
    client.post("/api/demo/reset")
    before = client.get(f"/api/stores/{DEMO_STORE_ID}/risk").json()["risk_score"]
    exception_id = client.get(f"/api/stores/{DEMO_STORE_ID}/exceptions").json()["exceptions"][0]["id"]
    client.post(f"/api/exceptions/{exception_id}/resolve", json={"action": "create_entry"})
    after = client.get(f"/api/stores/{DEMO_STORE_ID}/risk").json()["risk_score"]
    assert after < before, "resolving an exception must lower the notice risk"


def test_evidence_payload_meets_the_passport_contract() -> None:
    """SPEC §9: a source card must carry kind, filename, ref, extracted fields,
    confidence, and the model badge — otherwise the drawer cannot render."""
    client.post("/api/demo/reset")
    entries = client.get(f"/api/stores/{DEMO_STORE_ID}/ledger").json()["entries"]
    khaata = next(item for item in entries if item["source_kind"] == "khaata_photo")
    payload = client.get(f"/api/ledger-entries/{khaata['id']}/evidence").json()

    assert payload["ledger_entry"]["amount"].startswith("₹")
    assert payload["ledger_entry"]["party"]
    source = payload["sources"][0]
    for field in ("kind", "filename", "ref", "extracted", "confidence", "model"):
        assert field in source, f"source card is missing {field}"
    assert source["filename"] == "khaata_page_1.jpg"
    assert source["model"] == "gpt-4o"
    assert source["extracted"]["amount"] == payload["ledger_entry"]["amount"]
    assert payload["match_rule_plain_en"] and payload["match_rule_plain_hi"]


def test_evidence_for_a_matched_entry_names_the_rule_in_plain_language() -> None:
    client.post("/api/demo/reset")
    entries = client.get(f"/api/stores/{DEMO_STORE_ID}/ledger").json()["entries"]
    matched = next(item for item in entries if item["id"] == "invoice-INV-232")
    payload = client.get(f"/api/ledger-entries/{matched['id']}/evidence").json()
    assert payload["match_rule"] == "exact_amount_date"
    assert "amount and date" in payload["match_rule_plain_en"]
    assert len(payload["sources"]) == 2, "a matched pair must show both sides as evidence"
    assert {source["kind"] for source in payload["sources"]} == {"invoice_image", "upi_csv"}


def test_csv_export_has_one_row_per_ledger_entry_with_evidence_columns() -> None:
    import csv as csv_module
    import io

    client.post("/api/demo/reset")
    ledger = client.get(f"/api/stores/{DEMO_STORE_ID}/ledger").json()["entries"]
    response = client.get(f"/api/stores/{DEMO_STORE_ID}/export", params={"fmt": "csv"})
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    rows = list(csv_module.DictReader(io.StringIO(response.text)))
    assert len(rows) == len(ledger)
    assert "evidence_files" in rows[0] and "match_rule" in rows[0]
    assert any(row["match_rule"] for row in rows)
    assert all(row["amount_paise"].lstrip("-").isdigit() for row in rows)


def test_pdf_export_generates_a_non_empty_evidence_pack() -> None:
    client.post("/api/demo/reset")
    response = client.get(f"/api/stores/{DEMO_STORE_ID}/export", params={"fmt": "pdf"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
    assert len(response.content) > 2000


def test_export_rejects_an_unknown_format() -> None:
    assert client.get(f"/api/stores/{DEMO_STORE_ID}/export", params={"fmt": "docx"}).status_code == 422
