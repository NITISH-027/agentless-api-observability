import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import get_settings
from app.models.incident import Incident
from app.services.github.client import GitHubClient
from app.services.github.token_store import token_registry
from app.schemas.github_schemas import (
    ConnectRequest,
    ConnectResponse,
    RepositoryMetadata,
    AssociateRepoRequest
)

logger = logging.getLogger("app.api.routes.github_routes")
router = APIRouter()

def get_resolved_token(x_github_connection_id: Optional[str] = Header(None)) -> str:
    """
    Dependency to resolve the GitHub token. Checks custom connection ID,
    otherwise falls back to default GITHUB_TOKEN in env configuration.
    """
    if x_github_connection_id:
        token = token_registry.get_token(x_github_connection_id)
        if token:
            return token
            
    settings = get_settings()
    if settings.GITHUB_TOKEN and settings.GITHUB_TOKEN != "dummy_github_token":
        return settings.GITHUB_TOKEN
        
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="GitHub Token connection ID not provided or missing GITHUB_TOKEN configuration."
    )

@router.post("/github/connect", response_model=ConnectResponse)
async def connect_github(payload: ConnectRequest):
    """
    Verifies a user-provided GitHub Token. Returns a secure, server-side temporary
    connection ID if verification succeeds.
    """
    logger.info("Verifying user GitHub Token connection request")
    try:
        username = await GitHubClient.validate_token(payload.token)
        connection_id = token_registry.register(payload.token)
        logger.info(f"GitHub token verified for user '{username}'. Session Connection ID: {connection_id}")
        return ConnectResponse(connection_id=connection_id, username=username)
    except ValueError as e:
        logger.warning(f"GitHub connection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.get("/github/repositories", response_model=List[RepositoryMetadata])
async def list_github_repositories(token: str = Depends(get_resolved_token)):
    """
    Lists repositories accessible to the connected GitHub Token.
    """
    logger.info("Querying repository lists from GitHub API")
    try:
        repos_data = await GitHubClient.get_repositories(token)
        repos = []
        for repo in repos_data:
            repos.append(RepositoryMetadata(
                name=repo["name"],
                full_name=repo["full_name"],
                owner=repo["owner"]["login"],
                private=repo["private"],
                html_url=repo["html_url"],
                description=repo.get("description"),
                default_branch=repo.get("default_branch", "main")
            ))
        return repos
    except ValueError as e:
        logger.error(f"Failed to query user repositories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/incidents/{incident_id}/repository", response_model=None)
async def associate_repository(
    incident_id: str,
    payload: AssociateRepoRequest,
    token: str = Depends(get_resolved_token),
    db: Session = Depends(get_db)
):
    """
    Links a GitHub repository and target checkout commit to an incident record.
    """
    logger.info(f"Request to link repository {payload.owner}/{payload.repository} to incident {incident_id}")
    
    # 1. Fetch the incident
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID {incident_id} not found"
        )
        
    # 2. Verify repo access and metadata
    try:
        repo_meta = await GitHubClient.get_repository_metadata(token, payload.owner, payload.repository)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to retrieve repository metadata: {e}"
        )
        
    default_branch = repo_meta.get("default_branch", "main")
    target_branch = payload.branch or default_branch

    # 3. Determine and validate target commit SHA
    commit_sha = payload.commit_sha
    
    # Fallback to incident metadata if no SHA was supplied in body
    if not commit_sha and incident.metadata_json:
        commit_sha = incident.metadata_json.get("git_commit")
        
    # Fallback to branch head commit if still no SHA is resolved
    if not commit_sha:
        try:
            # Query commits on branch via GET /repos/{owner}/{repo}/commits/{branch}
            branch_commit = await GitHubClient.get_commit(token, payload.owner, payload.repository, target_branch)
            commit_sha = branch_commit["sha"]
            logger.info(f"Resolved branch head commit for '{target_branch}': {commit_sha}")
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to resolve head commit for branch '{target_branch}': {e}"
            )
            
    # Validate final commit SHA
    try:
        await GitHubClient.get_commit(token, payload.owner, payload.repository, commit_sha)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to validate commit SHA '{commit_sha}': {e}"
        )

    # 4. Clone repository into workspace
    try:
        from app.services.github.workspace import WorkspaceManager
        wm = WorkspaceManager()
        ws_id = f"ws_inc_{incident_id}"
        logger.info(f"Cloning associated repository to local workspace: {ws_id}")
        wm.clone_repository(
            token=token,
            owner=payload.owner,
            repo=payload.repository,
            commit_sha=commit_sha,
            branch=target_branch,
            workspace_id=ws_id
        )
    except Exception as e:
        logger.error(f"Failed to clone repository during association: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clone associated repository to workspace: {e}"
        )

    # 5. Save association details to database
    try:
        incident.github_owner = payload.owner
        incident.github_repo = payload.repository
        incident.github_branch = target_branch
        incident.github_commit_sha = commit_sha
        incident.github_repo_url = f"https://github.com/{payload.owner}/{payload.repository}"
        db.commit()
        logger.info(f"Incident {incident_id} successfully associated and cloned for {payload.owner}/{payload.repository} @ {commit_sha}")
        return {
            "status": "success",
            "incident_id": incident.id,
            "github_owner": incident.github_owner,
            "github_repo": incident.github_repo,
            "github_branch": incident.github_branch,
            "github_commit_sha": incident.github_commit_sha,
            "github_repo_url": incident.github_repo_url
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update incident record in database: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database write failed"
        )
