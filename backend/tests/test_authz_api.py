from fastapi.testclient import TestClient

from main import DEMO_STORE_ID, app


client = TestClient(app)


def test_health_reports_ready() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_anonymous_demo_store_is_available() -> None:
    response = client.post("/api/stores/demo")

    assert response.status_code == 200
    assert response.json()["store_id"] == DEMO_STORE_ID
    assert response.json()["is_public"] is True
