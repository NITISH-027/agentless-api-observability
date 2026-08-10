import pytest
import json
import subprocess
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.models.incident import Incident, InvestigationStatus
from app.services.github.pr_manager import PullRequestManager, sanitize_text
from app.services.github.workspace import WorkspaceManager

# ==========================================
# Unit Tests for Sanitization Filter
# ==========================================
def test_sanitize_text():
    raw_desc = """
    Incident occurred.
    Authorization: Bearer mySecretTokenabc123
    AWS_ACCESS_KEY_ID = "AKIA123EXAMPLE"
    password = 'mypassword123'
    client_secret: "secretval"
    """
    clean = sanitize_text(raw_desc)
    assert "Bearer mySecretTokenabc123" not in clean
    assert "AKIA123EXAMPLE" not in clean
    assert "mypassword123" not in clean
    assert "secretval" not in clean
    assert "[REDACTED]" in clean

# ==========================================
# Integration & Mock Tests for PR Manager
# ==========================================
def create_test_incident_for_pr(db_session, incident_id="inc_pr_test", patch_status="ACCEPTED", verified=True):
    db_incident = Incident(
        id=incident_id,
        fingerprint="fp_pr",
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
        traceback_analysis={
            "exception_type": "ValueError",
            "exception_message": "quantity negative",
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
        hypotheses=[
            {
                "id": "hyp_1",
                "title": "Negative Quantity Unchecked",
                "category": "CODE",
                "description": "Validation checks missing.",
                "verification": {
                    "verdict": "VALIDATED" if verified else "REJECTED",
                    "confidence": "HIGH"
                }
            }
        ],
        verification_results={
            "hyp_1": {
                "verdict": "VALIDATED" if verified else "REJECTED",
                "confidence": "HIGH"
            }
        } if verified else {},
        reproduction_result={
            "reproduced": True,
            "exception_type": "ValueError",
            "test_path": "reproduce_test.py",
            "workspace_id": "ws_repro_baseline"
        },
        patch_result={
            "status": patch_status,
            "patch_diff": "diff --git a/src/service.py\n+    if qty < 0: raise ValueError",
            "explanation": "Added check",
            "root_cause_addressed": "Validation check missing"
        } if patch_status else None
    )
    db_session.add(db_incident)
    db_session.commit()
    return db_incident

@pytest.fixture
def mock_wm():
    wm = MagicMock(spec=WorkspaceManager)
    wm.clone_repository.return_value = "ws_pr_verify"
    wm._get_repo_path.return_value = "/mock/workspace/repository"
    return wm

@pytest.mark.asyncio
async def test_pr_manager_gatekeeper_validation_failures(mock_wm, db_session):
    manager = PullRequestManager(workspace_manager=mock_wm)
    
    # 1. Test failure: No validated hypothesis
    inc_no_val = create_test_incident_for_pr(db_session, incident_id="inc_pr_fail_val", verified=False)
    with pytest.raises(ValueError) as exc_info:
        await manager.create_pull_request(db=db_session, incident_id=inc_no_val.id, token="mock_tok")
    assert "requires at least one experimentally VALIDATED hypothesis" in str(exc_info.value)
    
    # 2. Test failure: No generated/accepted patch
    inc_no_patch = create_test_incident_for_pr(db_session, incident_id="inc_pr_fail_patch", patch_status=None)
    with pytest.raises(ValueError) as exc_info:
        await manager.create_pull_request(db=db_session, incident_id=inc_no_patch.id, token="mock_tok")
    assert "requires a generated patch" in str(exc_info.value)

@pytest.mark.asyncio
@patch("subprocess.run")
@patch("httpx.AsyncClient.post")
@patch("httpx.AsyncClient.get")
async def test_pr_manager_creation_success(mock_get, mock_post, mock_sub, mock_wm, db_session):
    incident = create_test_incident_for_pr(db_session, incident_id="inc_pr_success")
    manager = PullRequestManager(workspace_manager=mock_wm)
    
    # Mock duplicate PR search returns empty list
    mock_get.return_value = MagicMock(status_code=200, json=lambda: [])
    
    # Mock pull request creation response
    mock_post.side_effect = [
        # PR post response
        MagicMock(status_code=201, json=lambda: {"number": 42, "html_url": "https://github.com/octocat/hello-world/pull/42"}),
        # Label post response
        MagicMock(status_code=200, json=lambda: {})
    ]
    
    # Mock subprocess git commands
    mock_sub.return_value = MagicMock(returncode=0)
    
    result = await manager.create_pull_request(db=db_session, incident_id=incident.id, token="mock_tok")
    
    assert result["status"] == "CREATED"
    assert result["pr_number"] == 42
    assert result["pr_url"] == "https://github.com/octocat/hello-world/pull/42"
    
    # Verify DB update
    updated_inc = db_session.query(Incident).filter(Incident.id == incident.id).first()
    assert updated_inc.status == InvestigationStatus.FIXED
    assert updated_inc.pr_result["pr_number"] == 42
    
    # Check that subprocess ran git branch checkout, config, add, commit, push
    # 6 calls: git config name, git config email, git checkout, apply_patch, git add, git commit, git push
    assert mock_sub.call_count >= 5

@pytest.mark.asyncio
@patch("subprocess.run")
@patch("httpx.AsyncClient.get")
async def test_pr_manager_duplicate_prevention(mock_get, mock_sub, mock_wm, db_session):
    incident = create_test_incident_for_pr(db_session, incident_id="inc_pr_duplicate")
    manager = PullRequestManager(workspace_manager=mock_wm)
    
    # Mock duplicate PR search returns active PR #12
    mock_get.return_value = MagicMock(
        status_code=200,
        json=lambda: [{"number": 12, "html_url": "https://github.com/octocat/hello-world/pull/12"}]
    )
    
    # Subprocess runs for branch setup / pushes
    mock_sub.return_value = MagicMock(returncode=0)
    
    result = await manager.create_pull_request(db=db_session, incident_id=incident.id, token="mock_tok")
    
    # Reuses existing PR #12 instead of creating a new one
    assert result["status"] == "CREATED"
    assert result["pr_number"] == 12
    assert result["pr_url"] == "https://github.com/octocat/hello-world/pull/12"

# API Endpoint route test
@patch("app.services.github.pr_manager.PullRequestManager.create_pull_request")
@patch("app.api.routes.logs.get_resolved_token")
def test_pull_request_endpoint_mock(mock_token, mock_pr, client: TestClient):
    mock_token.return_value = "mock_tok"
    mock_pr.return_value = {"status": "CREATED", "pr_number": 42, "pr_url": "https://github.com/.../42"}
    
    response = client.post(
        "/incidents/inc_123/pull-request",
        json={"connection_id": "conn_123"},
        headers={"x-github-connection-id": "conn_123"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "CREATED"
    assert response.json()["pr_number"] == 42
