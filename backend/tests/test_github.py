import os
import json
import pytest
import tempfile
import shutil
import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.services.github.workspace import WorkspaceManager
from app.services.github.token_store import token_registry
from app.services.github.client import GitHubClient
from app.models.incident import Incident, InvestigationStatus

# ==========================================
# Fixtures for Local Mock Git Repository
# ==========================================
@pytest.fixture
def mock_git_remote():
    """
    Sets up a temporary local Git repository to serve as a remote clone target.
    This enables real git subprocess tests without hitting the real network.
    """
    temp_dir = tempfile.mkdtemp()
    temp_path = Path(temp_dir)
    
    try:
        # Initialize repository
        subprocess.run(["git", "init"], check=True, cwd=str(temp_path), capture_output=True)
        # Configure dummy credentials for git operations
        subprocess.run(["git", "config", "user.name", "Tester"], check=True, cwd=str(temp_path), capture_output=True)
        subprocess.run(["git", "config", "user.email", "tester@example.com"], check=True, cwd=str(temp_path), capture_output=True)
        
        # Create a mock file and commit it
        file1 = temp_path / "src" / "index.py"
        file1.parent.mkdir(parents=True, exist_ok=True)
        file1.write_text("def run():\n    print('hello')\n", encoding="utf-8")
        
        subprocess.run(["git", "add", "."], check=True, cwd=str(temp_path), capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], check=True, cwd=str(temp_path), capture_output=True)
        
        # Get head commit SHA
        res = subprocess.run(["git", "rev-parse", "HEAD"], check=True, cwd=str(temp_path), capture_output=True, text=True)
        commit_sha = res.stdout.strip()
        
        yield temp_path, commit_sha
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

# ==========================================
# Workspace Git Subprocess tests
# ==========================================
def test_workspace_manager_flow(mock_git_remote, tmp_path):
    remote_path, commit_sha = mock_git_remote
    
    wm = WorkspaceManager(base_path=str(tmp_path))
    
    # Intercept clone url logic in WorkspaceManager to clone from file URL
    # instead of github.com
    original_run_git_cmd = wm._run_git_command
    def patched_run_git_cmd(cmd, cwd, token=None):
        modified_cmd = []
        for arg in cmd:
            if "github.com/" in arg:
                # Replace remote github URL with local path URL
                modified_cmd.append(str(remote_path))
            else:
                modified_cmd.append(arg)
        return original_run_git_cmd(modified_cmd, cwd, token)
        
    with patch.object(wm, "_run_git_command", side_effect=patched_run_git_cmd):
        workspace_id = wm.clone_repository(
            token="mock_token",
            owner="mock_owner",
            repo="mock_repo",
            commit_sha=commit_sha,
            branch="main"
        )
        
    # Verify metadata.json was written
    ws_path = tmp_path / workspace_id
    assert (ws_path / "metadata.json").exists()
    with open(ws_path / "metadata.json", "r") as f:
        meta = json.load(f)
        assert meta["owner"] == "mock_owner"
        assert meta["commit_sha"] == commit_sha
        
    # Verify file listing
    files = wm.list_files(workspace_id)
    assert "src/index.py" in files
    
    # Verify file reading
    content = wm.read_file(workspace_id, "src/index.py")
    assert "print('hello')" in content
    
    # Verify branch creation
    wm.create_branch(workspace_id, "feature/fix-bug")
    
    # Verify patch application
    patch_diff = """diff --git a/src/index.py b/src/index.py
index a1b2c3d..e4f5g6h 100644
--- a/src/index.py
+++ b/src/index.py
@@ -1,2 +1,3 @@
 def run():
     print('hello')
+    print('fixed')
"""
    wm.apply_patch(workspace_id, patch_diff)
    patched_content = wm.read_file(workspace_id, "src/index.py")
    assert "print('fixed')" in patched_content
    
    # Verify commit changes
    wm.commit_changes(workspace_id, "Apply patch fix", author_name="Agent fix", author_email="fix@agent.com")

# ==========================================
# Route Integration & Mock tests
# ==========================================
@patch("app.services.github.client.GitHubClient.validate_token")
def test_github_connect_success(mock_validate, client: TestClient):
    mock_validate.return_value = "octocat"
    
    response = client.post("/github/connect", json={"token": "ghp_securetoken"})
    assert response.status_code == 200
    data = response.json()
    assert "connection_id" in data
    assert data["username"] == "octocat"
    
    # Assert token was cached server-side
    assert token_registry.get_token(data["connection_id"]) == "ghp_securetoken"

@patch("app.services.github.client.GitHubClient.validate_token")
def test_github_connect_unauthorized(mock_validate, client: TestClient):
    mock_validate.side_effect = ValueError("Unauthorized or invalid GitHub token")
    
    response = client.post("/github/connect", json={"token": "ghp_badtoken"})
    assert response.status_code == 401
    assert "invalid GitHub token" in response.json()["detail"]

@patch("app.services.github.client.GitHubClient.get_repositories")
def test_list_github_repositories(mock_get_repos, client: TestClient):
    mock_get_repos.return_value = [
        {
            "name": "hello-world",
            "full_name": "octocat/hello-world",
            "owner": {"login": "octocat"},
            "private": False,
            "html_url": "https://github.com/octocat/hello-world",
            "description": "This is a test repo",
            "default_branch": "main"
        }
    ]
    
    # Register connection ID
    conn_id = token_registry.register("mock_tok")
    
    response = client.get("/github/repositories", headers={"x-github-connection-id": conn_id})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "hello-world"
    assert data[0]["owner"] == "octocat"

@patch("app.services.github.workspace.WorkspaceManager.clone_repository")
@patch("app.services.github.client.GitHubClient.get_repository_metadata")
@patch("app.services.github.client.GitHubClient.get_commit")
def test_associate_repository_success(mock_get_commit, mock_get_meta, mock_clone, client: TestClient, db_session):
    # Setup mock behaviors
    mock_clone.return_value = "ws_test"
    mock_get_meta.return_value = {"default_branch": "main"}
    mock_get_commit.return_value = {"sha": "abc123commitsha"}
    
    # 1. Insert dummy incident in database
    from datetime import datetime, timezone
    incident_id = "inc_testrepo"
    db_incident = Incident(
        id=incident_id,
        fingerprint="dummy_fp",
        service="payment-api",
        environment="staging",
        timestamp=datetime.now(timezone.utc),
        ingested_at=datetime.now(timezone.utc),
        status=InvestigationStatus.RECEIVED,
        request_method="GET",
        request_path="/pay",
        response_status_code=500,
        error_type="ConnectionError",
        error_message="failed to reach payment gateway",
        error_stack_trace="Traceback info here"
    )
    db_session.add(db_incident)
    db_session.commit()
    
    # Register connection ID
    conn_id = token_registry.register("mock_tok")

    # 2. Make association POST request
    assoc_body = {
        "owner": "octocat",
        "repository": "hello-world",
        "branch": "main",
        "commit_sha": "abc123commitsha"
    }
    
    response = client.post(
        f"/incidents/{incident_id}/repository",
        json=assoc_body,
        headers={"x-github-connection-id": conn_id}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["github_owner"] == "octocat"
    assert data["github_commit_sha"] == "abc123commitsha"
    
    # 3. Check DB update
    updated_inc = db_session.query(Incident).filter(Incident.id == incident_id).first()
    assert updated_inc.github_owner == "octocat"
    assert updated_inc.github_repo == "hello-world"
    assert updated_inc.github_commit_sha == "abc123commitsha"
    assert updated_inc.github_repo_url == "https://github.com/octocat/hello-world"

@patch("app.services.github.client.GitHubClient.get_repository_metadata")
def test_associate_repository_invalid_repo(mock_get_meta, client: TestClient, db_session):
    mock_get_meta.side_effect = ValueError("Repository 'octocat/hello' not found")
    
    # Insert incident
    from datetime import datetime, timezone
    incident_id = "inc_badrepo"
    db_incident = Incident(
        id=incident_id,
        fingerprint="dummy_fp2",
        service="payment-api",
        environment="staging",
        timestamp=datetime.now(timezone.utc),
        ingested_at=datetime.now(timezone.utc),
        status=InvestigationStatus.RECEIVED,
        request_method="GET",
        request_path="/pay",
        response_status_code=500,
        error_type="ConnectionError",
        error_message="failed to reach payment gateway",
        error_stack_trace="Traceback info here"
    )
    db_session.add(db_incident)
    db_session.commit()
    
    conn_id = token_registry.register("mock_tok")
    
    response = client.post(
        f"/incidents/{incident_id}/repository",
        json={"owner": "octocat", "repository": "hello"},
        headers={"x-github-connection-id": conn_id}
    )
    assert response.status_code == 400
    assert "Failed to retrieve repository metadata" in response.json()["detail"]
