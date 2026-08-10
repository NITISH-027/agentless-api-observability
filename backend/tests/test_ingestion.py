import pytest
from fastapi.testclient import TestClient

# Standard valid payload helper
def get_valid_payload():
    return {
        "service": "order-api",
        "environment": "production",
        "timestamp": "2026-08-10T10:30:00Z",
        "request": {
            "method": "POST",
            "path": "/api/orders/99",
            "query": {"ref": "web"},
            "headers": {
                "Authorization": "Bearer supersecrettoken",
                "Cookie": "session_id=abc12345",
                "Content-Type": "application/json"
            },
            "body": {"quantity": -5}
        },
        "response": {
            "status_code": 500,
            "body": {"error": "Internal Server Error"}
        },
        "error": {
            "type": "ValueError",
            "message": "quantity cannot be negative",
            "stack_trace": 'File "app/routes.py", line 42, in create_order\n    raise ValueError("quantity cannot be negative")'
        },
        "metadata": {
            "request_id": "req_123",
            "deployment_id": "deploy_456",
            "git_commit": "abc123"
        }
    }

def test_valid_log_ingestion(client: TestClient) -> None:
    """
    Verifies that a valid log payload is successfully accepted and returns 201.
    """
    payload = get_valid_payload()
    response = client.post("/logs", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert "incident_id" in data
    assert "fingerprint" in data
    assert data["status"] == "RECEIVED"
    assert data["service"] == "order-api"
    assert data["environment"] == "production"

def test_invalid_http_method(client: TestClient) -> None:
    """
    Verifies that invalid HTTP methods are rejected.
    """
    payload = get_valid_payload()
    payload["request"]["method"] = "INVALID_METHOD"
    
    response = client.post("/logs", json=payload)
    assert response.status_code == 422
    assert "method" in response.text

def test_invalid_status_code(client: TestClient) -> None:
    """
    Verifies that responses with status codes outside [100, 599] are rejected.
    """
    payload = get_valid_payload()
    payload["response"]["status_code"] = 999
    
    response = client.post("/logs", json=payload)
    assert response.status_code == 422
    assert "status_code" in response.text

def test_missing_stack_trace(client: TestClient) -> None:
    """
    Verifies that stack trace is a required, non-empty field.
    """
    payload = get_valid_payload()
    payload["error"]["stack_trace"] = "   " # whitespace only
    
    response = client.post("/logs", json=payload)
    assert response.status_code == 422
    assert "stack_trace" in response.text

def test_malformed_timestamp(client: TestClient) -> None:
    """
    Verifies that malformed ISO timestamps are rejected.
    """
    payload = get_valid_payload()
    payload["timestamp"] = "not-a-timestamp"
    
    response = client.post("/logs", json=payload)
    assert response.status_code == 422

def test_incident_retrieval(client: TestClient) -> None:
    """
    Verifies that ingested incidents can be retrieved by list and ID.
    """
    payload = get_valid_payload()
    ingest_resp = client.post("/logs", json=payload)
    assert ingest_resp.status_code == 201
    incident_id = ingest_resp.json()["incident_id"]

    # 1. Test GET /incidents (list)
    list_resp = client.get("/incidents")
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert len(list_data) >= 1
    
    # Assert fields are correctly mapped
    found = False
    for incident in list_data:
        if incident["id"] == incident_id:
            found = True
            assert incident["service"] == "order-api"
            assert incident["environment"] == "production"
            assert incident["error_type"] == "ValueError"
            break
    assert found

    # 2. Test GET /incidents/{incident_id}
    detail_resp = client.get(f"/incidents/{incident_id}")
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert detail_data["id"] == incident_id
    assert detail_data["request_method"] == "POST"
    assert detail_data["response_status_code"] == 500

    # 3. Test non-existent incident ID returns 404
    missing_resp = client.get("/incidents/inc_nonexistent")
    assert missing_resp.status_code == 404

def test_fingerprint_duplicate_detection(client: TestClient) -> None:
    """
    Verifies that different logs with similar stable characteristics
    generate the exact same fingerprint, enabling deduplication.
    """
    payload_1 = get_valid_payload()
    # Normalize route test: order-api has "/api/orders/99" and "/api/orders/10"
    payload_2 = get_valid_payload()
    payload_2["request"]["path"] = "/api/orders/10" # should normalize to /api/orders/:id
    payload_2["timestamp"] = "2026-08-10T10:35:00Z" # different timestamp
    payload_2["metadata"]["request_id"] = "req_999" # different request ID

    resp_1 = client.post("/logs", json=payload_1)
    resp_2 = client.post("/logs", json=payload_2)
    
    assert resp_1.status_code == 201
    assert resp_2.status_code == 201
    
    fp_1 = resp_1.json()["fingerprint"]
    fp_2 = resp_2.json()["fingerprint"]
    assert fp_1 == fp_2

def test_sensitive_header_filtering(client: TestClient) -> None:
    """
    Verifies that headers like Authorization, Cookie, and X-API-Key are scrubbed to [FILTERED].
    """
    payload = get_valid_payload()
    payload["request"]["headers"] = {
        "Authorization": "Bearer originalsecrettoken",
        "Cookie": "secret_session=val",
        "X-API-Key": "mykey",
        "Content-Type": "application/json"
    }

    ingest_resp = client.post("/logs", json=payload)
    assert ingest_resp.status_code == 201
    incident_id = ingest_resp.json()["incident_id"]

    # Fetch incident details from API to inspect headers
    detail_resp = client.get(f"/incidents/{incident_id}")
    assert detail_resp.status_code == 200
    headers = detail_resp.json()["request_headers"]
    
    assert headers["Authorization"] == "[FILTERED]"
    assert headers["Cookie"] == "[FILTERED]"
    assert headers["X-API-Key"] == "[FILTERED]"
    assert headers["Content-Type"] == "application/json"  # non-sensitive remains intact
