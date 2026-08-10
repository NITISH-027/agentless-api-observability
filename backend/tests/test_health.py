from fastapi.testclient import TestClient

def test_health_endpoint(client: TestClient) -> None:
    """
    Verifies that the /health endpoint is operational and returns {"status": "ok"}.
    """
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data == {"status": "ok"}
