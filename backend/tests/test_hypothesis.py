import pytest
import json
import asyncio
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.models.incident import Incident, InvestigationStatus
from app.services.analysis.llm_provider import MockLLMProvider
from app.services.analysis.hypothesis_generator import HypothesisGenerator, HypothesisList
from app.services.github.workspace import WorkspaceManager

# Helper to create a basic incident record
def create_test_incident(db_session, incident_id="inc_hyp_test"):
    db_incident = Incident(
        id=incident_id,
        fingerprint="fp_hyp",
        service="order-api",
        environment="production",
        timestamp=datetime.now(timezone.utc),
        ingested_at=datetime.now(timezone.utc),
        status=InvestigationStatus.RECEIVED,
        request_method="POST",
        request_path="/api/orders",
        response_status_code=500,
        error_type="ValueError",
        error_message="quantity negative",
        error_stack_trace="Traceback details",
        traceback_analysis={
            "exception_type": "ValueError",
            "exception_message": "quantity negative",
            "files_in_traceback": ["src/service.py"],
            "frames": [
                {
                    "mapped": True,
                    "repo_path": "src/service.py",
                    "line_number": 87,
                    "function_name": "create_order",
                    "context": []
                }
            ]
        }
    )
    db_session.add(db_incident)
    db_session.commit()
    return db_incident

# Mock Workspace files list helper
@pytest.fixture
def mock_wm():
    wm = MagicMock(spec=WorkspaceManager)
    wm.list_files.return_value = ["src/service.py", "src/router.py", "utils/helper.py"]
    return wm

# Valid mock json output matching the schema
VALID_HYPOTHESIS_JSON = json.dumps({
    "hypotheses": [
        {
            "id": "hyp_1",
            "title": "Unvalidated Negative Quantity",
            "category": "CODE",
            "description": "Negative quantity parameter is sent directly to calculate_total() function which causes errors.",
            "affected_files": ["src/service.py"],
            "affected_lines": [87],
            "supporting_evidence": ["POST body contains quantity=-5", "Stack trace ends inside create_order()"],
            "contradicting_evidence": [],
            "confidence": "HIGH",
            "verification_plan": ["Send quantity=-5 request to verified client route", "Assert client returns status 400"]
        }
    ]
})

@pytest.mark.asyncio
async def test_generate_hypotheses_valid(mock_wm, db_session):
    incident = create_test_incident(db_session)
    provider = MockLLMProvider(response_text=VALID_HYPOTHESIS_JSON)
    
    generator = HypothesisGenerator(workspace_manager=mock_wm)
    hypotheses = await generator.generate_hypotheses(
        db=db_session,
        incident_id=incident.id,
        workspace_id="ws_test",
        provider=provider
    )
    
    assert len(hypotheses) == 1
    assert hypotheses[0]["id"] == "hyp_1"
    assert hypotheses[0]["category"] == "CODE"
    assert hypotheses[0]["affected_files"] == ["src/service.py"]
    
    # Assert DB update
    updated_inc = db_session.query(Incident).filter(Incident.id == incident.id).first()
    assert updated_inc.hypotheses is not None
    assert updated_inc.hypotheses[0]["id"] == "hyp_1"

@pytest.mark.asyncio
async def test_generate_hypotheses_malformed_retry_failure(mock_wm, db_session):
    incident = create_test_incident(db_session, incident_id="inc_malformed")
    
    # Bad JSON missing required fields
    bad_json = '{"hypotheses": [{"id": "hyp_1", "title": "Missing attributes"}]}'
    provider = MockLLMProvider(response_text=bad_json)
    
    generator = HypothesisGenerator(workspace_manager=mock_wm)
    
    with pytest.raises(ValueError) as exc_info:
        await generator.generate_hypotheses(
            db=db_session,
            incident_id=incident.id,
            workspace_id="ws_test",
            provider=provider,
            max_retries=2
        )
    assert "Failed to generate structured hypotheses" in str(exc_info.value)
    
    # Check that it did not save anything to DB
    updated_inc = db_session.query(Incident).filter(Incident.id == incident.id).first()
    assert updated_inc.hypotheses is None

@pytest.mark.asyncio
async def test_generate_hypotheses_hallucinated_file(mock_wm, db_session):
    incident = create_test_incident(db_session, incident_id="inc_hallucinate")
    
    # Referencing a file not in mock_wm list (src/hallucinated.py)
    hallucinated_json = json.dumps({
        "hypotheses": [
            {
                "id": "hyp_1",
                "title": "Database Config",
                "category": "CONFIG",
                "description": "Config is wrong.",
                "affected_files": ["src/hallucinated.py"],  # Hallucinated file
                "affected_lines": [10],
                "supporting_evidence": [],
                "contradicting_evidence": [],
                "confidence": "LOW",
                "verification_plan": ["Verify config"]
            }
        ]
    })
    provider = MockLLMProvider(response_text=hallucinated_json)
    generator = HypothesisGenerator(workspace_manager=mock_wm)
    
    with pytest.raises(ValueError) as exc_info:
        await generator.generate_hypotheses(
            db=db_session,
            incident_id=incident.id,
            workspace_id="ws_test",
            provider=provider,
            max_retries=1
        )
    assert "Hallucinated file paths detected" in str(exc_info.value)

@pytest.mark.asyncio
async def test_generate_hypotheses_provider_failure(mock_wm, db_session):
    incident = create_test_incident(db_session, incident_id="inc_prov_fail")
    provider = MockLLMProvider(simulate_failure=True)
    generator = HypothesisGenerator(workspace_manager=mock_wm)
    
    with pytest.raises(ValueError) as exc_info:
        await generator.generate_hypotheses(
            db=db_session,
            incident_id=incident.id,
            workspace_id="ws_test",
            provider=provider,
            max_retries=1
        )
    assert "Simulated API connection failure" in str(exc_info.value)

@pytest.mark.asyncio
async def test_generate_hypotheses_timeout(mock_wm, db_session):
    incident = create_test_incident(db_session, incident_id="inc_timeout")
    provider = MockLLMProvider(simulate_timeout=True)
    generator = HypothesisGenerator(workspace_manager=mock_wm)
    
    with pytest.raises(ValueError) as exc_info:
        await generator.generate_hypotheses(
            db=db_session,
            incident_id=incident.id,
            workspace_id="ws_test",
            provider=provider,
            max_retries=1
        )
    assert "Simulated API timeout" in str(exc_info.value)

# Endpoint route test
@patch("app.services.analysis.hypothesis_generator.HypothesisGenerator.generate_hypotheses")
@patch("app.api.routes.logs.get_settings")
def test_hypotheses_endpoint_mock(mock_get_settings, mock_gen, client: TestClient):
    mock_gen.return_value = [{"id": "hyp_1", "title": "Mocked Hyp"}]
    
    mock_settings = MagicMock()
    mock_settings.LLM_PROVIDER = "mock"
    mock_settings.LLM_API_KEY = "mock_key"
    mock_get_settings.return_value = mock_settings
    
    response = client.post(
        "/incidents/inc_123/hypotheses",
        json={"workspace_id": "ws_123", "provider": "mock"}
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == "hyp_1"

