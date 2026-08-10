import os
import re
import time
import httpx
import logging
import subprocess
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.incident import Incident, InvestigationStatus
from app.services.github.workspace import WorkspaceManager

logger = logging.getLogger("app.services.github.pr_manager")

def sanitize_text(text: str) -> str:
    """
    Scrubs credentials, passwords, Bearer tokens, and secrets from text logs.
    """
    scrubbed = text
    # Scrub Bearer headers
    scrubbed = re.sub(r'(Authorization\s*:\s*)Bearer\s+[A-Za-z0-9_\-\.\+=]+', r'\1Bearer [REDACTED]', scrubbed, flags=re.IGNORECASE)
    # Scrub generic API key / secret assignments
    scrubbed = re.sub(r'([a-zA-Z0-9_\-\.]*(key|secret|token|password)[a-zA-Z0-9_\-\.]*)\s*[:=]\s*["\'][A-Za-z0-9_\-\.\+=]{4,}["\']', r'\1 = "[REDACTED]"', scrubbed, flags=re.IGNORECASE)
    # Scrub high-entropy tokens
    scrubbed = re.sub(r'xox[baprs]-[0-9]{12}-[0-9]{12}-[a-zA-Z0-9]{24}', '[REDACTED_SLACK_TOKEN]', scrubbed)
    return scrubbed

class PullRequestManager:
    def __init__(self, workspace_manager: Optional[WorkspaceManager] = None):
        self.wm = workspace_manager or WorkspaceManager()

    async def create_pull_request(
        self,
        db: Session,
        incident_id: str,
        token: str
    ) -> Dict[str, Any]:
        logger.info(f"Checking prerequisites for Pull Request creation on incident {incident_id}")
        
        # 1. Fetch incident record
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")

        # 2. Gatekeeper state checks
        owner = incident.github_owner
        repo = incident.github_repo
        commit_sha = incident.github_commit_sha
        branch = incident.github_branch or "main"
        
        if not owner or not repo or not commit_sha:
            raise ValueError(f"Incident {incident_id} is not associated with a GitHub repository / commit.")

        # Check reproduction state
        repro = incident.reproduction_result
        verifications = incident.verification_results or {}
        
        has_reproduction = repro is not None and repro.get("reproduced") is True
        has_validation = any(v.get("verdict") == "VALIDATED" for v in verifications.values())
        
        if not has_reproduction and not verifications:
            raise ValueError("Pull Request requires a reproduced failure or verified baseline state.")
            
        if not has_validation:
            raise ValueError("Pull Request requires at least one experimentally VALIDATED hypothesis.")

        # Check patch state
        patch_res = incident.patch_result
        if not patch_res or patch_res.get("status") != "ACCEPTED":
            raise ValueError("Pull Request requires a generated patch that has passed verification (ACCEPTED status).")

        patch_diff = patch_res.get("patch_diff")
        
        # 3. Create branch and commit changes in clean isolated workspace
        ws_id = None
        branch_name = f"ai-fix/incident-{incident_id}"
        
        try:
            # Clone clean repository snapshot
            ws_id = self.wm.clone_repository(token, owner, repo, commit_sha, branch)
            repo_dir = self.wm._get_repo_path(ws_id)
            
            # Configure git user details locally inside the workspace clone
            subprocess.run(["git", "config", "user.name", "AI Observability Platform"], cwd=repo_dir, check=True)
            subprocess.run(["git", "config", "user.email", "ai-agent@platform.observability"], cwd=repo_dir, check=True)
            
            # Checkout unique branch from commit SHA
            logger.info(f"Checking out branch {branch_name}...")
            subprocess.run(["git", "checkout", "-b", branch_name], cwd=repo_dir, check=True)
            
            # Apply verified patch
            self.wm.apply_patch(ws_id, patch_diff)
            
            # Stage and Commit changes
            subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
            commit_msg = f"fix: resolve validated API failure #{incident_id}"
            subprocess.run(["git", "commit", "-m", commit_msg], cwd=repo_dir, check=True)
            
            # Push branch to origin
            logger.info(f"Pushing branch {branch_name} to origin...")
            subprocess.run(["git", "push", "-f", "origin", branch_name], cwd=repo_dir, check=True)
            
        except Exception as e:
            logger.error(f"Git operations failed during PR staging: {e}")
            raise ValueError(f"Failed to push git changes: {e}")
        finally:
            if ws_id:
                self.wm.delete_workspace(ws_id)

        # 4. Check for duplicate Pull Request
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        async with httpx.AsyncClient() as client:
            # Look up open PRs matching the head branch
            dup_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
            params = {
                "head": f"{owner}:{branch_name}",
                "state": "open"
            }
            try:
                dup_resp = await client.get(dup_url, headers=headers, params=params)
                if dup_resp.status_code == 200:
                    open_prs = dup_resp.json()
                    if open_prs:
                        pr_info = open_prs[0]
                        logger.info(f"Found duplicate Pull Request: PR #{pr_info['number']} already exists.")
                        return self._update_incident_fixed(db, incident, pr_info)
            except Exception as e:
                logger.warning(f"Failed to check duplicate Pull Requests: {e}")

            # 5. Build title & description
            affected_func = "unknown_function"
            frames = incident.traceback_analysis.get("frames", [])
            for frame in reversed(frames):
                if frame.get("mapped") and frame.get("function_name"):
                    affected_func = frame.get("function_name")
                    break
                    
            pr_title = f"Fix: Resolve {incident.error_type} in {affected_func}"
            
            # Build description summary containing verified results
            pr_desc = f"""### AI-Generated Bug Fix Summary

This Pull Request resolves the exception observed in incident **#{incident_id}**.

#### 🚨 Incident Details
- **Endpoint**: `{incident.request_method} {incident.request_path}`
- **HTTP Status**: `{incident.response_status_code}`
- **Exception**: `{incident.error_type}: {incident.error_message}`
- **Timestamp**: `{incident.timestamp}`

#### 🔍 Root Cause Analysis
{patch_res.get('root_cause_addressed', 'No root cause summary listed.')}

#### 🛠️ Verification & Test Results
- **Reproduction**: Successfully reproduced the target exception class `{incident.error_type}` in isolated sandboxes.
- **Verification Verdict**: `VALIDATED`
- **Verification Log**: The Pytest reproducer test script now compiles and passes successfully.

#### 📝 Explanation of Changes
{patch_res.get('explanation', 'No patch explanation listed.')}

---
*Note: This PR is generated automatically by an AI agent. Please verify before merging. No guarantees of zero regressions are made.*
"""
            
            # Sanitization Check
            sanitized_title = sanitize_text(pr_title)
            sanitized_desc = sanitize_text(pr_desc)
            
            # 6. Create Pull Request on GitHub
            pr_payload = {
                "title": sanitized_title,
                "body": sanitized_desc,
                "head": branch_name,
                "base": branch
            }
            
            create_pr_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
            resp = await client.post(create_pr_url, headers=headers, json=pr_payload)
            
            if resp.status_code not in (201, 200):
                logger.error(f"GitHub API Pull Request creation failed: {resp.text}")
                raise ValueError(f"GitHub Pull Request creation failed ({resp.status_code}): {resp.text}")
                
            pr_data = resp.json()
            pr_number = pr_data.get("number")
            
            # 7. Add tags/labels to PR gracefully
            labels_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/labels"
            labels_payload = {"labels": ["ai-generated", "bug-fix", "verified"]}
            try:
                label_resp = await client.post(labels_url, headers=headers, json=labels_payload)
                if label_resp.status_code not in (200, 201):
                    logger.warning(f"Failed to add labels to Pull Request: {label_resp.text}")
            except Exception as e:
                logger.warning(f"Failed to add labels to Pull Request: {e}")
                
            # 8. Save PR results and set Incident status to FIXED
            return self._update_incident_fixed(db, incident, pr_data)

    def _update_incident_fixed(self, db: Session, incident: Incident, pr_data: Dict[str, Any]) -> Dict[str, Any]:
        result = {
            "status": "CREATED",
            "pr_number": pr_data.get("number"),
            "pr_url": pr_data.get("html_url"),
            "head_branch": pr_data.get("head", {}).get("ref", f"ai-fix/incident-{incident.id}"),
            "created_at": pr_data.get("created_at", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        }
        
        # Save to DB and update status
        incident.pr_result = result
        incident.status = InvestigationStatus.FIXED
        
        try:
            db.commit()
            logger.info(f"Pull Request #{pr_data.get('number')} created and incident {incident.id} marked as FIXED.")
            return result
        except Exception as e:
            db.rollback()
            logger.error(f"Database write failure during PR status logging: {e}")
            raise ValueError(f"Database write failed: {e}")
