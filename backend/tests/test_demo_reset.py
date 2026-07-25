from fastapi.testclient import TestClient

from main import DEMO_STORE_ID, app


def test_demo_reset_restores_open_seeded_exceptions() -> None:
    client = TestClient(app)
    client.post(f"/api/stores/{DEMO_STORE_ID}/reconcile")
    exception_id = client.get(f"/api/stores/{DEMO_STORE_ID}/exceptions").json()["exceptions"][0]["id"]
    client.post(f"/api/exceptions/{exception_id}/resolve", json={"action": "ask_user"})

    response = client.post("/api/demo/reset")

    assert response.status_code == 200
    exceptions = client.get(f"/api/stores/{DEMO_STORE_ID}/exceptions").json()["exceptions"]
    assert len(exceptions) == 4
    assert {item["status"] for item in exceptions} == {"open"}
