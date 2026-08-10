import pytest
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.models.incident import Incident, InvestigationStatus
from app.services.patch.patch_generator import PatchGenerator, contains_secrets, contains_suspicious_files
from app.services.github.workspace import WorkspaceManager
from app.services.reproduction.sandbox import SandboxExecutor
from app.services.analysis.llm_provider import MockLLMProvider

# ==========================================
# Unit Tests for Safety Scanners
# ==========================================
def test_contains_secrets_detector():
    clean_diff = "+++ a/src/service.py\n+    if qty < 0: raise ValueError"
    assert contains_secrets(clean_diff) is False
    
    secret_diff_1 = '+++ a/src/service.py\n+    AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"'
    assert contains_secrets(secret_diff_1) is True
    
    secret_diff_2 = '+++ a/src/service.py\n+    stripe_api_key = "sk_test_51Cs2f3g4h5j6"'
    assert contains_secrets(secret_diff_2) is True

def test_contains_suspicious_files():
    clean_files = ["src/service.py", "src/orders.py"]
    assert contains_suspicious_files(clean_files) is False
    
    dirty_files_1 = ["src/service.py", ".env"]
    assert contains_suspicious_files(dirty_files_1) is True
    
    dirty_files_2 = ["Dockerfile", "src/service.py"]
    assert contains_suspicious_files(dirty_files_2) is True

# ==========================================
# Integration & Mock Tests for Patch Engine
# ==========================================
def create_test_incident_with_validated_hyp(db_session, incident_id="inc_patch_test"):
    db_incident = Incident(
        id=incident_id,
        fingerprint="fp_patch",
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
        },
        github_owner="octocat",
        github_repo="hello-world",
        github_commit_sha="abc123commit",
        github_repo_url="https://github.com/octocat/hello-world",
        hypotheses=[
            {
                "id": "hyp_1",
                "title": "Negative Quantity Unchecked",
                "category": "CODE",
                "description": "Validation checks missing.",
                "verification": {
                    "verdict": "VALIDATED",
                    "confidence": "HIGH",
                    "reason": "Passed."
                }
            }
        ],
        verification_results={
            "hyp_1": {
                "verdict": "VALIDATED",
                "confidence": "HIGH",
                "reason": "Passed."
            }
        },
        reproduction_result={
            "reproduced": True,
            "exception_type": "ValueError",
            "test_path": "reproduce_test.py",
            "workspace_id": "ws_repro_baseline"
        }
    )
    db_session.add(db_incident)
    db_session.commit()
    return db_incident

@pytest.fixture
def mock_wm():
    wm = MagicMock(spec=WorkspaceManager)
    wm.clone_repository.return_value = "ws_patch_verify"
    wm.read_file.return_value = "def test_reproduce(): pass"
    return wm

# Valid mock json output matching PatchModel schema
VALID_PATCH_JSON = json.dumps({
    "files_to_modify": ["src/service.py"],
    "patch_diff": "diff --git a/src/service.py b/src/service.py\n+    if qty < 0: raise ValueError",
    "explanation": "Added validations.",
    "root_cause_addressed": "Validation check missing",
    "tests_added_or_modified": [],
    "risk_notes": "Low risk"
})

@pytest.mark.asyncio
@patch("app.services.reproduction.sandbox.SandboxExecutor.run_test")
async def test_patch_engine_validated_success(mock_run, mock_wm, db_session):
    incident = create_test_incident_with_validated_hyp(db_session, incident_id="inc_pat_ok")
    
    # Mock reproducer executes and passes (exit_code=0)
    mock_run.return_value = {"success": True, "exit_code": 0, "stdout": "test passed", "stderr": "", "duration_ms": 150}
    provider = MockLLMProvider(response_text=VALID_PATCH_JSON)
    
    generator = PatchGenerator(workspace_manager=mock_wm)
    result = await generator.generate_and_verify_patch(
        db=db_session,
        incident_id=incident.id,
        hypothesis_id="hyp_1",
        token="mock_tok",
        provider=provider
    )
    
    assert result["status"] == "ACCEPTED"
    assert result["files_to_modify"] == ["src/service.py"]
    
    # Assert DB update
    updated_inc = db_session.query(Incident).filter(Incident.id == incident.id).first()
    assert updated_inc.status == InvestigationStatus.FIXED
    assert updated_inc.patch_result["status"] == "ACCEPTED"
    
    # Assert temporary workspace deletion
    mock_wm.delete_workspace.assert_called_with("ws_patch_verify")

@pytest.mark.asyncio
async def test_patch_engine_non_validated_hypothesis(mock_wm, db_session):
    # Setup incident where hypothesis is NOT validated
    incident = create_test_incident_with_validated_hyp(db_session, incident_id="inc_pat_not_val")
    # Reset verdict to REJECTED
    incident.verification_results = {"hyp_1": {"verdict": "REJECTED"}}
    db_session.commit()
    
    generator = PatchGenerator(workspace_manager=mock_wm)
    with pytest.raises(ValueError) as exc_info:
        await generator.generate_and_verify_patch(
            db=db_session,
            incident_id=incident.id,
            hypothesis_id="hyp_1",
            token="mock_tok",
            provider=MockLLMProvider()
        )
    assert "has not been validated" in str(exc_info.value)

@pytest.mark.asyncio
async def test_patch_engine_secret_detected(mock_wm, db_session):
    incident = create_test_incident_with_validated_hyp(db_session, incident_id="inc_pat_secret")
    
    # Mock LLM returns diff containing AWS secret key assignment
    secret_patch = json.dumps({
        "files_to_modify": ["src/service.py"],
        "patch_diff": 'diff --git a/src/service.py\n+    AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"',
        "explanation": "Added key.",
        "root_cause_addressed": "Validation check missing",
        "tests_added_or_modified": [],
        "risk_notes": "Low"
    })
    provider = MockLLMProvider(response_text=secret_patch)
    
    generator = PatchGenerator(workspace_manager=mock_wm)
    result = await generator.generate_and_verify_patch(
        db=db_session,
        incident_id=incident.id,
        hypothesis_id="hyp_1",
        token="mock_tok",
        provider=provider
    )
    
    assert result["status"] == "PATCH_VERIFICATION_FAILED"
    assert "Secrets or API keys detected" in result["reason"]

@pytest.mark.asyncio
async def test_patch_engine_suspicious_files(mock_wm, db_session):
    incident = create_test_incident_with_validated_hyp(db_session, incident_id="inc_pat_suspicious")
    
    # Mock LLM returns diff modifying Dockerfile
    suspicious_patch = json.dumps({
        "files_to_modify": ["Dockerfile", "src/service.py"],
        "patch_diff": "diff --git a/Dockerfile",
        "explanation": "Update config.",
        "root_cause_addressed": "Validation check missing",
        "tests_added_or_modified": [],
        "risk_notes": "Low"
    })
    provider = MockLLMProvider(response_text=suspicious_patch)
    
    generator = PatchGenerator(workspace_manager=mock_wm)
    result = await generator.generate_and_verify_patch(
        db=db_session,
        incident_id=incident.id,
        hypothesis_id="hyp_1",
        token="mock_tok",
        provider=provider
    )
    
    assert result["status"] == "PATCH_VERIFICATION_FAILED"
    assert "critical system files blocked" in result["reason"]

@pytest.mark.asyncio
async def test_patch_engine_patch_conflict(mock_wm, db_session):
    incident = create_test_incident_with_validated_hyp(db_session, incident_id="inc_pat_conflict")
    
    # Mock Git patch apply failure
    mock_wm.apply_patch.side_effect = ValueError("Merge conflict")
    provider = MockLLMProvider(response_text=VALID_PATCH_JSON)
    
    generator = PatchGenerator(workspace_manager=mock_wm)
    result = await generator.generate_and_verify_patch(
        db=db_session,
        incident_id=incident.id,
        hypothesis_id="hyp_1",
        token="mock_tok",
        provider=provider
    )
    
    assert result["status"] == "PATCH_VERIFICATION_FAILED"
    assert "Patch failed to apply cleanly" in result["reason"]

@pytest.mark.asyncio
@patch("app.services.reproduction.sandbox.SandboxExecutor.run_test")
async def test_patch_engine_reproducer_failing(mock_run, mock_wm, db_session):
    incident = create_test_incident_with_validated_hyp(db_session, incident_id="inc_pat_test_fail")
    
    # Mock reproducer executes but still fails (exit_code=1)
    mock_run.return_value = {"success": True, "exit_code": 1, "stdout": "ValueError: negative quantity", "stderr": "", "duration_ms": 100}
    provider = MockLLMProvider(response_text=VALID_PATCH_JSON)
    
    generator = PatchGenerator(workspace_manager=mock_wm)
    result = await generator.generate_and_verify_patch(
        db=db_session,
        incident_id=incident.id,
        hypothesis_id="hyp_1",
        token="mock_tok",
        provider=provider
    )
    
    assert result["status"] == "PATCH_VERIFICATION_FAILED"
    assert "reproducer test execution failed" in result["reason"]

# ==========================================
# Route API test
# ==========================================
@patch("app.services.patch.patch_generator.PatchGenerator.generate_and_verify_patch")
@patch("app.api.routes.logs.get_resolved_token")
@patch("app.api.routes.logs.get_settings")
def test_patch_endpoint_mock(mock_settings, mock_token, mock_patch, client: TestClient):
    mock_token.return_value = "mock_tok"
    mock_patch.return_value = {"status": "ACCEPTED"}
    
    m_set = MagicMock()
    m_set.LLM_PROVIDER = "mock"
    m_set.LLM_API_KEY = "mock_key"
    mock_settings.return_value = m_set
    
    response = client.post(
        "/incidents/inc_123/patch",
        json={"hypothesis_id": "hyp_1", "provider": "mock"},
        headers={"x-github-connection-id": "conn_123"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ACCEPTED"
