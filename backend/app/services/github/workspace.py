import os
import re
import json
import uuid
import shutil
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger("app.services.github.workspace")

class WorkspaceManager:
    """
    Manages isolated workspace environments in the filesystem (under `d:/Agentless/workspace`).
    Supports safe git checkouts, cloning, branching, reading files, patching, and committing.
    """
    def __init__(self, base_path: Optional[str] = None):
        if base_path:
            self.base_path = Path(base_path).resolve()
        else:
            # Default to root project workspace folder
            self.base_path = Path(__file__).resolve().parent.parent.parent.parent.parent / "workspace"
        self.base_path.mkdir(exist_ok=True, parents=True)

    def _get_workspace_path(self, workspace_id: str) -> Path:
        return self.base_path / workspace_id

    def _get_repo_path(self, workspace_id: str) -> Path:
        return self._get_workspace_path(workspace_id) / "repository"

    def _run_git_command(self, cmd: List[str], cwd: Path, token: Optional[str] = None) -> str:
        """
        Executes a git command via subprocess, sanitizing stdout/stderr
        to prevent token leakage in logs and exception traces.
        """
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True, cwd=str(cwd))
            return result.stdout
        except subprocess.CalledProcessError as e:
            # Sanitize stderr and stdout
            stderr = e.stderr or ""
            stdout = e.stdout or ""
            cmd_str = " ".join(e.cmd)
            
            if token:
                stderr = stderr.replace(token, "[FILTERED]")
                stdout = stdout.replace(token, "[FILTERED]")
                cmd_str = cmd_str.replace(token, "[FILTERED]")
                
            logger.error(f"Git execution failure: {cmd_str}\nStderr: {stderr}")
            raise ValueError(f"Git command failed: {stderr.strip() or stdout.strip() or str(e)}")

    def clone_repository(
        self,
        token: str,
        owner: str,
        repo: str,
        commit_sha: str,
        branch: Optional[str] = None,
        workspace_id: Optional[str] = None
    ) -> str:
        """
        Clones a repository into an isolated workspace directory and checks out the specific commit.
        Returns the generated workspace_id.
        """
        if not workspace_id:
            workspace_id = f"ws_{uuid.uuid4().hex[:16]}"
        ws_dir = self._get_workspace_path(workspace_id)
        ws_dir.mkdir(exist_ok=True, parents=True)
        
        repo_dir = ws_dir / "repository"
        repo_dir.mkdir(exist_ok=True)

        logger.info(f"Cloning {owner}/{repo} (Commit: {commit_sha}) into isolated workspace {workspace_id}")
        
        # Git clone using token authentication
        clone_url = f"https://x-access-token:{token}@github.com/{owner}/{repo}.git"
        
        # 1. Clone the repository without checkouts initially (speeds up checkout)
        clone_cmd = ["git", "clone", "--no-checkout", clone_url, "."]
        self._run_git_command(clone_cmd, cwd=repo_dir, token=token)

        # 2. Checkout the specific commit SHA
        actual_sha = commit_sha
        try:
            checkout_cmd = ["git", "checkout", commit_sha]
            self._run_git_command(checkout_cmd, cwd=repo_dir, token=token)
        except Exception as e:
            logger.warning(f"Failed to checkout commit {commit_sha}: {e}. Falling back to branch '{branch or 'main'}'.")
            fallback_branch = branch or "main"
            try:
                checkout_cmd = ["git", "checkout", fallback_branch]
                self._run_git_command(checkout_cmd, cwd=repo_dir, token=token)
            except Exception as e2:
                logger.warning(f"Failed to checkout branch '{fallback_branch}': {e2}. Falling back to HEAD.")
                try:
                    checkout_cmd = ["git", "checkout", "HEAD"]
                    self._run_git_command(checkout_cmd, cwd=repo_dir, token=token)
                except Exception as e3:
                    logger.error(f"Fallback checkouts failed: {e3}")

        try:
            actual_sha_cmd = ["git", "rev-parse", "HEAD"]
            actual_sha = self._run_git_command(actual_sha_cmd, cwd=repo_dir).strip()
            logger.info(f"Workspace resolved to actual commit SHA: {actual_sha}")
        except Exception as e_rev:
            logger.warning(f"Failed to resolve HEAD commit SHA: {e_rev}")

        # 3. Create metadata file
        metadata = {
            "workspace_id": workspace_id,
            "owner": owner,
            "repository": repo,
            "commit_sha": actual_sha,
            "branch": branch or "main",
            "created_at": Path(ws_dir).stat().st_ctime
        }
        with open(ws_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        return workspace_id

    def checkout_commit(self, workspace_id: str, commit_sha: str) -> None:
        """
        Checks out an arbitrary commit inside the workspace repository.
        """
        repo_dir = self._get_repo_path(workspace_id)
        if not repo_dir.exists():
            raise FileNotFoundError(f"Workspace {workspace_id} repository does not exist")
            
        checkout_cmd = ["git", "checkout", commit_sha]
        self._run_git_command(checkout_cmd, cwd=repo_dir)

    def read_file(self, workspace_id: str, relative_path: str) -> str:
        """
        Reads files from the isolated workspace clone.
        """
        repo_dir = self._get_repo_path(workspace_id)
        file_path = (repo_dir / relative_path).resolve()
        
        # Secure boundary check: verify file is strictly inside repo directory to prevent path traversal
        if not str(file_path).startswith(str(repo_dir)):
            raise ValueError("Path traversal violation: file is outside workspace repository")

        if not file_path.exists():
            raise FileNotFoundError(f"File {relative_path} does not exist in workspace {workspace_id}")
            
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    def list_files(self, workspace_id: str) -> List[str]:
        """
        Recursively lists relative paths of all files in the workspace (excluding .git folder).
        """
        repo_dir = self._get_repo_path(workspace_id)
        if not repo_dir.exists():
            raise FileNotFoundError(f"Workspace {workspace_id} repository does not exist")
            
        file_list = []
        for root, dirs, files in os.walk(repo_dir):
            # Ignore .git directory
            if ".git" in dirs:
                dirs.remove(".git")
            for file in files:
                full_path = Path(root) / file
                relative = full_path.relative_to(repo_dir)
                file_list.append(str(relative).replace("\\", "/"))
                
        return file_list

    def create_branch(self, workspace_id: str, branch_name: str) -> None:
        """
        Creates and switches to a new Git branch inside the workspace.
        """
        repo_dir = self._get_repo_path(workspace_id)
        if not repo_dir.exists():
            raise FileNotFoundError(f"Workspace {workspace_id} repository does not exist")
            
        branch_cmd = ["git", "checkout", "-b", branch_name]
        self._run_git_command(branch_cmd, cwd=repo_dir)

    def apply_patch(self, workspace_id: str, patch_content: str) -> None:
        """
        Applies a unified patch diff to the workspace repository code.
        """
        ws_dir = self._get_workspace_path(workspace_id)
        repo_dir = self._get_repo_path(workspace_id)
        if not repo_dir.exists():
            raise FileNotFoundError(f"Workspace {workspace_id} repository does not exist")

        # Write patch file in the workspace (not inside repository itself to keep git status clean)
        patch_file = ws_dir / "change.patch"
        with open(patch_file, "w", encoding="utf-8", newline="\n") as f:
            f.write(patch_content)

        try:
            # Apply patch using git apply
            apply_cmd = ["git", "apply", str(patch_file)]
            self._run_git_command(apply_cmd, cwd=repo_dir)
        finally:
            # Clean up the patch file
            if patch_file.exists():
                os.remove(patch_file)

    def commit_changes(
        self,
        workspace_id: str,
        message: str,
        author_name: str = "Agentless Platform",
        author_email: str = "debugger@agentless.platform"
    ) -> None:
        """
        Stages and commits all modifications inside the repository workspace.
        """
        repo_dir = self._get_repo_path(workspace_id)
        if not repo_dir.exists():
            raise FileNotFoundError(f"Workspace {workspace_id} repository does not exist")

        # 1. Add all changed/untracked files
        add_cmd = ["git", "add", "-A"]
        self._run_git_command(add_cmd, cwd=repo_dir)

        # 2. Configure user name & email for this repository session
        self._run_git_command(["git", "config", "user.name", author_name], cwd=repo_dir)
        self._run_git_command(["git", "config", "user.email", author_email], cwd=repo_dir)

        # 3. Commit the changes
        commit_cmd = ["git", "commit", "-m", message]
        self._run_git_command(commit_cmd, cwd=repo_dir)

    def push_branch(self, token: str, workspace_id: str, branch_name: str) -> None:
        """
        Pushes the branch changes to the remote repository.
        """
        repo_dir = self._get_repo_path(workspace_id)
        if not repo_dir.exists():
            raise FileNotFoundError(f"Workspace {workspace_id} repository does not exist")

        # Push branch to origin
        push_cmd = ["git", "push", "origin", branch_name]
        self._run_git_command(push_cmd, cwd=repo_dir, token=token)

    def delete_workspace(self, workspace_id: str) -> None:
        """
        Deletes the entire workspace directory including checkout files.
        """
        ws_dir = self._get_workspace_path(workspace_id)
        if ws_dir.exists():
            # In Windows, git files are sometimes read-only which breaks shutil.rmtree.
            # Handle read-only file removal gracefully.
            def handle_onerror(func, path, exc_info):
                import stat
                try:
                    if not os.access(path, os.W_OK):
                        os.chmod(path, stat.S_IWUSR)
                        func(path)
                except Exception as e:
                    logger.warning(f"Failed to force remove path {path}: {e}")
            try:
                shutil.rmtree(ws_dir, onerror=handle_onerror)
            except Exception as e:
                logger.warning(f"Could not fully delete workspace directory {ws_dir}: {e}")

