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
