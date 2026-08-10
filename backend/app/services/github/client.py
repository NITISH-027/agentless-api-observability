import httpx
from typing import Dict, Any, List

class GitHubClient:
    """
    Communicates with the GitHub API to validate credentials, retrieve repository metadata,
    inspect commits, and read remote source files.
    """
    @staticmethod
    async def validate_token(token: str) -> str:
        """
        Validates the user token via GET /user.
        Returns the username if valid; otherwise raises ValueError.
        """
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AgentlessPlatform"
        }
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get("https://api.github.com/user", headers=headers)
                if resp.status_code == 200:
                    return resp.json()["login"]
                elif resp.status_code == 401:
                    raise ValueError("Invalid GitHub Token")
                else:
                    raise ValueError(f"GitHub API returned unexpected status code: {resp.status_code}")
            except httpx.RequestError as e:
                raise ValueError(f"Failed to connect to GitHub API: {e}")

    @staticmethod
    async def get_repository_metadata(token: str, owner: str, repo: str) -> Dict[str, Any]:
        """
        Retrieves repository details from GET /repos/{owner}/{repo}.
        """
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AgentlessPlatform"
        }
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"https://api.github.com/repos/{owner}/{repo}", headers=headers)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 404:
                    raise ValueError(f"Repository '{owner}/{repo}' not found or unauthorized")
                else:
                    raise ValueError(f"GitHub API returned error status: {resp.status_code}")
            except httpx.RequestError as e:
                raise ValueError(f"Failed to connect to GitHub API: {e}")

    @staticmethod
    async def get_commit(token: str, owner: str, repo: str, commit_sha: str) -> Dict[str, Any]:
        """
        Inspects details of a specific commit SHA from GET /repos/{owner}/{repo}/commits/{commit_sha}.
        """
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AgentlessPlatform"
        }
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}",
                    headers=headers
                )
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 404:
                    raise ValueError(f"Commit '{commit_sha}' not found in '{owner}/{repo}'")
                else:
                    raise ValueError(f"GitHub API returned error status: {resp.status_code}")
            except httpx.RequestError as e:
                raise ValueError(f"Failed to connect to GitHub API: {e}")

    @staticmethod
    async def get_file_content(token: str, owner: str, repo: str, path: str, ref: str) -> str:
        """
        Fetches the raw contents of a remote file from GET /repos/{owner}/{repo}/contents/{path}?ref={ref}.
        """
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3.raw",
            "User-Agent": "AgentlessPlatform"
        }
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={ref}",
                    headers=headers
                )
                if resp.status_code == 200:
                    return resp.text
                elif resp.status_code == 404:
                    raise ValueError(f"File '{path}' not found at ref '{ref}'")
                else:
                    raise ValueError(f"GitHub API returned error status: {resp.status_code}")
            except httpx.RequestError as e:
                raise ValueError(f"Failed to connect to GitHub API: {e}")

    @staticmethod
    async def get_repositories(token: str) -> List[Dict[str, Any]]:
        """
        Lists repositories accessible to the provided token from GET /user/repos.
        """
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "AgentlessPlatform"
        }
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get("https://api.github.com/user/repos?per_page=100", headers=headers)
                if resp.status_code == 200:
                    return resp.json()
                else:
                    raise ValueError(f"GitHub API returned error status: {resp.status_code}")
            except httpx.RequestError as e:
                raise ValueError(f"Failed to connect to GitHub API: {e}")
