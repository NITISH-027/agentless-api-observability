import pytest
import json
import os
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.models.incident import Incident, InvestigationStatus
from app.services.verification.verifier import VerificationEngine, detects_symptom_suppression
from app.services.github.workspace import WorkspaceManager
from app.services.reproduction.sandbox import SandboxExecutor

# ==========================================
# Unit Tests for Symptom Suppression
# ==========================================
def test_detects_symptom_suppression_positive():
    suppress_patch = """diff --git a/src/service.py b/src/service.py
--- a/src/service.py
+++ b/src/service.py
@@ -10,3 +10,6 @@
+    try:
+        calculate_total()
+    except Exception:
+        pass
"""
    assert detects_symptom_suppression(suppress_patch) is True

    suppress_patch_2 = """diff --git a/src/service.py b/src/service.py
--- a/src/service.py
+++ b/src/service.py
@@ -10,3 +10,6 @@
+    try:
+        calculate_total()
+    except:
+        return {}
"""
    assert detects_symptom_suppression(suppress_patch_2) is True

def test_detects_symptom_suppression_negative():
    valid_patch = """diff --git a/src/service.py b/src/service.py
--- a/src/service.py
+++ b/src/service.py
@@ -10,3 +10,6 @@
+    if quantity < 0:
+        raise ValueError("quantity cannot be negative")
+    calculate_total()
"""
    assert detects_symptom_suppression(valid_patch) is False

# ==========================================
# Integration & Mock Tests for Verifier
# ==========================================
def create_test_incident_with_repro(db_session, reproduced=True, incident_id="inc_verify_test"):
    db_incident = Incident(
        id=incident_id,
        fingerprint="fp_verify",
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
                "verification": None
            }
        ],
        reproduction_result={
            "reproduced": reproduced,
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
    wm.clone_repository.return_value = "ws_verify_temp"
    wm.read_file.return_value = "def test_reproduce(): pass"
    return wm

@pytest.mark.asyncio
@patch("app.services.reproduction.sandbox.SandboxExecutor.run_test")
async def test_verifier_valid_fix(mock_run, mock_wm, db_session):
    incident = create_test_incident_with_repro(db_session, incident_id="inc_ver_ok")
    
    # Mock sandbox returns exit_code=0 (test passed)
    mock_run.return_value = {"success": True, "exit_code": 0, "stdout": "test passed", "stderr": "", "duration_ms": 100}
    
    verifier = VerificationEngine(workspace_manager=mock_wm)
    patch_code = "+++ add check code"
    
    result = await verifier.verify_hypothesis_patch(
        db=db_session,
        incident_id=incident.id,
        hypothesis_id="hyp_1",
        patch_content=patch_code,
        token="mock_tok"
    )
    
    assert result["verdict"] == "VALIDATED"
    assert result["confidence"] == "HIGH"
    
    # Verify DB update
    updated_inc = db_session.query(Incident).filter(Incident.id == incident.id).first()
    assert updated_inc.verification_results["hyp_1"]["verdict"] == "VALIDATED"
    assert updated_inc.hypotheses[0]["verification"]["verdict"] == "VALIDATED"
    
    # Assert temporary workspace deletion
    mock_wm.delete_workspace.assert_called_with("ws_verify_temp")

@pytest.mark.asyncio
@patch("app.services.reproduction.sandbox.SandboxExecutor.run_test")
async def test_verifier_symptom_suppression(mock_run, mock_wm, db_session):
    incident = create_test_incident_with_repro(db_session, incident_id="inc_ver_suppress")
    
    # Mock sandbox returns exit_code=0 (test passed)
    mock_run.return_value = {"success": True, "exit_code": 0, "stdout": "test passed", "stderr": "", "duration_ms": 100}
    
    verifier = VerificationEngine(workspace_manager=mock_wm)
    suppress_patch = "+    except Exception:\n+        pass"
    
    result = await verifier.verify_hypothesis_patch(
        db=db_session,
        incident_id=incident.id,
        hypothesis_id="hyp_1",
        patch_content=suppress_patch,
        token="mock_tok"
    )
    
    # Should reject due to symptom suppression even though test passed
    assert result["verdict"] == "REJECTED"
    assert "suppresses the symptom" in result["reason"]

@pytest.mark.asyncio
@patch("app.services.reproduction.sandbox.SandboxExecutor.run_test")
async def test_verifier_broken_patch(mock_run, mock_wm, db_session):
    incident = create_test_incident_with_repro(db_session, incident_id="inc_ver_broken")
    
    # Mock sandbox returns exit_code=1 with new NameError
    mock_run.return_value = {
        "success": True,
        "exit_code": 1,
        "stdout": "NameError: name 'x' is not defined",
        "stderr": "",
        "duration_ms": 100
    }
    
    verifier = VerificationEngine(workspace_manager=mock_wm)
    result = await verifier.verify_hypothesis_patch(
        db=db_session,
        incident_id=incident.id,
        hypothesis_id="hyp_1",
        patch_content="+++ buggy code",
        token="mock_tok"
    )
    
    assert result["verdict"] == "REJECTED"
    assert "NameError" in result["reason"]

@pytest.mark.asyncio
@patch("app.services.reproduction.sandbox.SandboxExecutor.run_test")
async def test_verifier_timeout(mock_run, mock_wm, db_session):
    incident = create_test_incident_with_repro(db_session, incident_id="inc_ver_timeout")
    
    # Mock sandbox timeout
    mock_run.return_value = {
        "success": False,
        "exit_code": -1,
        "stdout": "",
        "stderr": "timeout expired",
        "duration_ms": 5000,
        "reason": "Timeout expired"
    }
    
    verifier = VerificationEngine(workspace_manager=mock_wm)
    result = await verifier.verify_hypothesis_patch(
        db=db_session,
        incident_id=incident.id,
        hypothesis_id="hyp_1",
        patch_content="+++ infinite loop code",
        token="mock_tok"
    )
    
    assert result["verdict"] == "REJECTED"
    assert "timed out" in result["reason"]

@pytest.mark.asyncio
async def test_verifier_inconclusive_baseline(mock_wm, db_session):
    # Setup incident where baseline was NOT reproduced
    incident = create_test_incident_with_repro(db_session, reproduced=False, incident_id="inc_ver_incon")
    
    verifier = VerificationEngine(workspace_manager=mock_wm)
    result = await verifier.verify_hypothesis_patch(
        db=db_session,
        incident_id=incident.id,
        hypothesis_id="hyp_1",
        patch_content="+++ some patch",
        token="mock_tok"
    )
    
    assert result["verdict"] == "INCONCLUSIVE"

@pytest.mark.asyncio
async def test_verifier_patch_apply_conflict(mock_wm, db_session):
    incident = create_test_incident_with_repro(db_session, incident_id="inc_ver_conflict")
    
    # Mock patch apply failure
    mock_wm.apply_patch.side_effect = ValueError("Git patch conflicts")
    
    verifier = VerificationEngine(workspace_manager=mock_wm)
    result = await verifier.verify_hypothesis_patch(
        db=db_session,
        incident_id=incident.id,
        hypothesis_id="hyp_1",
        patch_content="+++ conflict patch",
        token="mock_tok"
    )
    
    assert result["verdict"] == "REJECTED"
    assert "failed to apply" in result["reason"]

# API Router test
@patch("app.services.verification.verifier.VerificationEngine.verify_hypothesis_patch")
@patch("app.api.routes.logs.get_resolved_token")
def test_verify_endpoint_mock(mock_token, mock_verify, client: TestClient):
    mock_token.return_value = "mock_tok"
    mock_verify.return_value = {"verdict": "VALIDATED", "confidence": "HIGH"}
    
    response = client.post(
        "/incidents/inc_123/verify",
        json={"hypothesis_id": "hyp_1", "patch_content": "+++ patch code"},
        headers={"x-github-connection-id": "conn_123"}
    )
    assert response.status_code == 200
    assert response.json()["verdict"] == "VALIDATED"
    assert response.json()["confidence"] == "HIGH"
