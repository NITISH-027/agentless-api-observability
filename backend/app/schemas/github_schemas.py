from pydantic import BaseModel, Field
from typing import Optional, List

class ConnectRequest(BaseModel):
    token: str = Field(..., description="GitHub Personal Access Token or App Installation Token")

class ConnectResponse(BaseModel):
    connection_id: str = Field(..., description="Secure session connection identifier")
    username: str = Field(..., description="Validated GitHub handle")

class RepositoryMetadata(BaseModel):
    name: str
    full_name: str
    owner: str
    private: bool
    html_url: str
    description: Optional[str] = None
    default_branch: str

class AssociateRepoRequest(BaseModel):
    owner: str = Field(..., description="GitHub account/org owner name")
    repository: str = Field(..., description="GitHub repository name")
    branch: Optional[str] = Field(None, description="Optional target branch (e.g. main, dev)")
    commit_sha: Optional[str] = Field(None, description="Optional git commit hash SHA")
