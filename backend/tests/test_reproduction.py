import pytest
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.models.incident import Incident, InvestigationStatus
from app.services.reproduction.sandbox import SandboxExecutor
from app.services.reproduction.manager import ReproductionManager
from app.services.github.workspace import WorkspaceManager
from app.services.analysis.llm_provider import MockLLMProvider

# ==========================================
# Unit Tests for Sandbox Executor
# ==========================================
def test_sandbox_executor_success(tmp_path):
    # Setup a dummy workspace directory
    ws_dir = tmp_path / "ws_success"
    repo_dir = ws_dir / "repository"
    repo_dir.mkdir(parents=True)
    
    # Create a failing pytest reproducer
    test_code = """
def test_failing_run():
    raise ValueError("target failure message")
"""
    (repo_dir / "reproduce_test.py").write_text(test_code, encoding="utf-8")
    
    executor = SandboxExecutor(allow_local_fallback=True)
    run_res = executor.run_test(
        workspace_path=ws_dir,
        test_relative_path="reproduce_test.py",
        timeout=10.0
    )
    
    assert run_res["success"] is True
    assert run_res["exit_code"] != 0  # test failed
    assert "ValueError" in run_res["stdout"] or "ValueError" in run_res["stderr"]
    assert run_res["duration_ms"] > 0

def test_sandbox_executor_timeout(tmp_path):
    # Setup a dummy workspace directory
    ws_dir = tmp_path / "ws_timeout"
    repo_dir = ws_dir / "repository"
    repo_dir.mkdir(parents=True)
    
    # Create an infinite sleep test
    test_code = """
import time
def test_infinite_run():
    time.sleep(5)
"""
    (repo_dir / "reproduce_test.py").write_text(test_code, encoding="utf-8")
    
    executor = SandboxExecutor(allow_local_fallback=True)
    # Set a tiny timeout
    run_res = executor.run_test(
        workspace_path=ws_dir,
        test_relative_path="reproduce_test.py",
        timeout=1.0
    )
    
    assert run_res["success"] is False
    assert run_res["exit_code"] == -1
    assert "TIMEOUT" in run_res["stderr"] or "Timeout" in run_res["reason"]

# ==========================================
# Integration Tests for Reproduction Manager
# ==========================================
def create_test_incident(db_session, incident_id="inc_repro_test"):
    db_incident = Incident(
        id=incident_id,
        fingerprint="fp_repro",
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
            "frames": []
        }
    )
    db_session.add(db_incident)
    db_session.commit()
    return db_incident

@pytest.fixture
def mock_wm(tmp_path):
    # Mock workspace manager referencing a real temporary directory on host
    wm = MagicMock(spec=WorkspaceManager)
    
    # Ensure directories exist
    repo_dir = tmp_path / "repository"
    repo_dir.mkdir(exist_ok=True)
    
    wm._get_workspace_path.return_value = tmp_path
    wm._get_repo_path.return_value = repo_dir
    wm.list_files.return_value = ["src/service.py"]
    return wm

@pytest.mark.asyncio
async def test_reproduction_flow_success(mock_wm, db_session):
    incident = create_test_incident(db_session, incident_id="inc_repro_ok")
    
    # Mock LLM returns test code that raises ValueError
    test_code_json = json.dumps({
        "test_code": "def test_fail():\n    raise ValueError('quantity negative')\n"
    })
    provider = MockLLMProvider(response_text=test_code_json)
    
    # Force sandbox local fallback for testing environment
    os.environ["ALLOW_LOCAL_SANDBOX_FALLBACK"] = "true"
    
    manager = ReproductionManager(workspace_manager=mock_wm)
    result = await manager.reproduce_incident(
        db=db_session,
        incident_id=incident.id,
        workspace_id="ws_test",
        provider=provider
    )
    
    assert result["reproduced"] is True
    assert result["exception_type"] == "ValueError"
    assert result["exception_message"] == "quantity negative"
    
    # Check DB update
    updated_inc = db_session.query(Incident).filter(Incident.id == incident.id).first()
    assert updated_inc.status == InvestigationStatus.REPRODUCING
    assert updated_inc.reproduction_result["reproduced"] is True

@pytest.mark.asyncio
async def test_reproduction_flow_unmatched_exception(mock_wm, db_session):
    incident = create_test_incident(db_session, incident_id="inc_repro_unmatched")
    
    # Mock LLM returns test code that raises TypeError instead of expected ValueError
    test_code_json = json.dumps({
        "test_code": "def test_fail():\n    raise TypeError('wrong type')\n"
    })
    provider = MockLLMProvider(response_text=test_code_json)
    
    manager = ReproductionManager(workspace_manager=mock_wm)
    result = await manager.reproduce_incident(
        db=db_session,
        incident_id=incident.id,
        workspace_id="ws_test",
        provider=provider
    )
    
    assert result["reproduced"] is False
    assert "test failed but expected exception type was missing" in result["reason"]
    
    # Check DB status
    updated_inc = db_session.query(Incident).filter(Incident.id == incident.id).first()
    assert updated_inc.status == InvestigationStatus.FAILED

@pytest.mark.asyncio
async def test_reproduction_flow_passed_test(mock_wm, db_session):
    incident = create_test_incident(db_session, incident_id="inc_repro_passed")
    
    # Mock LLM returns test code that passes (does not raise any exception)
    test_code_json = json.dumps({
        "test_code": "def test_pass():\n    pass\n"
    })
    provider = MockLLMProvider(response_text=test_code_json)
    
    manager = ReproductionManager(workspace_manager=mock_wm)
    result = await manager.reproduce_incident(
        db=db_session,
        incident_id=incident.id,
        workspace_id="ws_test",
        provider=provider
    )
    
    assert result["reproduced"] is False
    assert "test execution succeeded without raising target exception" in result["reason"]

# ==========================================
# Route API test
# ==========================================
@patch("app.services.reproduction.manager.ReproductionManager.reproduce_incident")
@patch("app.api.routes.logs.get_settings")
def test_reproduce_endpoint_mock(mock_get_settings, mock_repro, client: TestClient):
    mock_repro.return_value = {"reproduced": True, "exception_type": "ValueError"}
    
    mock_settings = MagicMock()
    mock_settings.LLM_PROVIDER = "mock"
    mock_settings.LLM_API_KEY = "mock_key"
    mock_get_settings.return_value = mock_settings
    
    response = client.post(
        "/incidents/inc_123/reproduce",
        json={"workspace_id": "ws_123", "provider": "mock"}
    )
    assert response.status_code == 200
    assert response.json()["reproduced"] is True
    assert response.json()["exception_type"] == "ValueError"
