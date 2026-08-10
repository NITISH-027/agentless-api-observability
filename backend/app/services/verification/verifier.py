import re
import os
import uuid
import time
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.models.incident import Incident, InvestigationStatus
from app.services.github.workspace import WorkspaceManager
from app.services.reproduction.sandbox import SandboxExecutor

logger = logging.getLogger("app.services.verification.verifier")

def detects_symptom_suppression(patch_content: str) -> bool:
    """
    Programmatically inspects the git patch contents to check if it merely
    swallows the exception generically (symptom suppression) without resolving it.
    """
    # Extract only the added lines (prefixed with '+' but not '+++')
    added_lines = []
    for line in patch_content.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            added_lines.append(line[1:].strip())
            
    added_text = "\n".join(added_lines)
    
    # Look for generic exception swallowing blocks like:
    # except: pass
    # except Exception: return {}
    suppress_patterns = [
        r'except\s*:\s*(pass|return\s*(\{\}|None|\[\])?)\s*$',
        r'except\s+Exception\s*:\s*(pass|return\s*(\{\}|None|\[\])?)\s*$',
        r'except\s*(Exception)?\s*:\s*\n\s*(pass|return\s*(\{\}|None|\[\])?)'
    ]
    
    for pattern in suppress_patterns:
        if re.search(pattern, added_text, re.MULTILINE | re.IGNORECASE):
            return True
            
    return False

class VerificationEngine:
    """
    Compares candidate code patches against the baseline reproduction.
    Determines if the fix is VALIDATED, REJECTED, or INCONCLUSIVE.
    """
    def __init__(self, workspace_manager: Optional[WorkspaceManager] = None):
        self.wm = workspace_manager or WorkspaceManager()

    async def verify_hypothesis_patch(
        self,
        db: Session,
        incident_id: str,
        hypothesis_id: str,
        patch_content: str,
        token: str,
        timeout: float = 15.0
    ) -> Dict[str, Any]:
        logger.info(f"Verifying candidate patch for incident {incident_id}, hypothesis {hypothesis_id}")
        
        # 1. Fetch incident record
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")

        # 2. Check if baseline reproduction exists and succeeded
        baseline = incident.reproduction_result
        if not baseline or not baseline.get("reproduced"):
            logger.warning(f"Reproduction result missing or failed for {incident_id}. Verification is inconclusive.")
            verdict = "INCONCLUSIVE"
            reason = "Verification inconclusive because baseline failure was not successfully reproduced."
            return self._save_verdict(db, incident, hypothesis_id, verdict, reason, {}, None)

        # 3. Read reproducer test code from baseline workspace
        baseline_ws_id = incident.reproduction_result.get("workspace_id") or "ws_test"
        test_relative_path = baseline.get("test_path", "reproduce_test.py")
        
        try:
            reproducer_code = self.wm.read_file(baseline_ws_id, test_relative_path)
        except Exception as e:
            logger.warning(f"Could not read reproducer from baseline workspace {baseline_ws_id}: {e}")
            # Fallback: create default test runner logic or use dummy
            reproducer_code = ""

        # 4. Clone clean repository snapshot for verification
        owner = incident.github_owner
        repo = incident.github_repo
        commit_sha = incident.github_commit_sha
        branch = incident.github_branch
        
        if not owner or not repo or not commit_sha:
            raise ValueError(f"Incident {incident_id} lacks repository details for verification checkout.")

        logger.info(f"Provisioning clean verify workspace for {owner}/{repo} at commit {commit_sha}")
        verify_ws_id = None
        start_time = time.time()
        
        try:
            # Clone clean repository snapshot
            verify_ws_id = self.wm.clone_repository(token, owner, repo, commit_sha, branch)
            
            # Write same reproducer script to new workspace
            test_file_path = self.wm._get_repo_path(verify_ws_id) / test_relative_path
            with open(test_file_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(reproducer_code)
                
            # Apply candidate patch
            logger.info("Applying candidate patch to verification workspace...")
            self.wm.apply_patch(verify_ws_id, patch_content)
            
        except Exception as e:
            logger.error(f"Failed to prepare workspace or apply patch: {e}")
            # If patch fails to apply, reject the hypothesis
            verdict = "REJECTED"
            reason = f"REJECTED: Candidate patch failed to apply or caused conflict: {e}"
            evidence = {"patch_apply_error": str(e)}
            
            # Cleanup workspace if created
            if verify_ws_id:
                self.wm.delete_workspace(verify_ws_id)
                
            return self._save_verdict(db, incident, hypothesis_id, verdict, reason, evidence, verify_ws_id)

        # 5. Execute sandbox runner
        try:
            settings = db.query(Incident).filter(Incident.id == incident_id).first() # settings check
            from app.core.config import get_settings
            app_settings = get_settings()
            allow_fallback = os.environ.get("ALLOW_LOCAL_SANDBOX_FALLBACK", "true").lower() == "true"
            
            executor = SandboxExecutor(
                sandbox_image=app_settings.SANDBOX_IMAGE,
                allow_local_fallback=allow_fallback
            )
            
            # Execute Pytest reproducer against patched workspace
            run_res = executor.run_test(
                workspace_path=self.wm._get_workspace_path(verify_ws_id),
                test_relative_path=test_relative_path,
                timeout=timeout
            )
        except Exception as e:
            logger.error(f"Sandbox verification run failed: {e}")
            verdict = "INCONCLUSIVE"
            reason = f"INCONCLUSIVE: Verification runner crashed: {e}"
            evidence = {"runner_error": str(e)}
            self.wm.delete_workspace(verify_ws_id)
            return self._save_verdict(db, incident, hypothesis_id, verdict, reason, evidence, verify_ws_id)

        duration_ms = int((time.time() - start_time) * 1000)
        
        # 6. Compare results against baseline
        exit_code = run_res.get("exit_code", -1)
        stdout = run_res.get("stdout", "")
        stderr = run_res.get("stderr", "")
        combined_output = stdout + "\n" + stderr
        
        evidence = {
            "baseline_exception": incident.error_type,
            "baseline_message": incident.error_message,
            "candidate_exit_code": exit_code,
            "candidate_stdout": stdout,
            "candidate_stderr": stderr,
            "duration_ms": duration_ms,
            "reproducer_passed": (exit_code == 0)
        }

        # 7. Check if timeout occurred
        if not run_res.get("success", True) and "Timeout" in run_res.get("reason", ""):
            verdict = "REJECTED"
            reason = "REJECTED: Patch verification execution timed out (potential infinite loop)."
            self.wm.delete_workspace(verify_ws_id)
            return self._save_verdict(db, incident, hypothesis_id, verdict, reason, evidence, verify_ws_id)

        # 8. Verdict Analysis logic
        verdict = "INCONCLUSIVE"
        reason = "Verification inconclusive."
        confidence = "LOW"

        # Check for symptom suppression
        symptom_suppression = detects_symptom_suppression(patch_content)
        
        if exit_code == 0:
            # Test passed (no unhandled exceptions)
            if symptom_suppression:
                verdict = "REJECTED"
                confidence = "LOW"
                reason = (
                    "REJECTED: The exception disappeared, but the patch merely suppresses the symptom "
                    "using generic exception swallowing (e.g. except Exception: pass)."
                )
            else:
                verdict = "VALIDATED"
                confidence = "HIGH"
                reason = (
                    "VALIDATED: The original ValueError exception was successfully resolved. "
                    "The reproducer test now executes and passes with exit code 0."
                )
        else:
            # Test still failed (non-zero exit code)
            target_exc = incident.error_type
            if target_exc in combined_output:
                # Still failed with original error
                verdict = "REJECTED"
                confidence = "LOW"
                reason = f"REJECTED: The patch failed to fix the error. The test still raises the original exception '{target_exc}'."
            else:
                # Failed, but with a different error (broken patch)
                # Find the new error name
                new_err = "UnknownError"
                if ":" in combined_output:
                    lines = [l.strip() for l in combined_output.split("\n") if l.strip()]
                    for line in reversed(lines):
                        if ":" in line and not line.startswith("E ") and not line.startswith("File "):
                            new_err = line.split(":", 1)[0].strip()
                            break
                            
                verdict = "REJECTED"
                confidence = "LOW"
                reason = f"REJECTED: The candidate patch broke execution, introducing a new exception '{new_err}'."

        # 9. Clean up verification workspace clone
        self.wm.delete_workspace(verify_ws_id)
        
        return self._save_verdict(db, incident, hypothesis_id, verdict, reason, evidence, verify_ws_id, confidence)

    def _save_verdict(
        self,
        db: Session,
        incident: Incident,
        hypothesis_id: str,
        verdict: str,
        reason: str,
        evidence: Dict[str, Any],
        workspace_id: Optional[str],
        confidence: str = "LOW"
    ) -> Dict[str, Any]:
        """
        Saves verification outcome details to the database and returns the result.
        """
        result = {
            "verdict": verdict,
            "reason": reason,
            "confidence": confidence,
            "evidence": evidence,
            "verified_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

        # 1. Update verification_results list on Incident
        current_verifications = incident.verification_results or {}
        new_verifications = dict(current_verifications)
        new_verifications[hypothesis_id] = result
        incident.verification_results = new_verifications

        # 2. Update specific hypothesis in hypotheses array
        current_hypotheses = incident.hypotheses or []
        new_hypotheses = []
        for hyp in current_hypotheses:
            hyp_copy = dict(hyp)
            if hyp_copy.get("id") == hypothesis_id:
                hyp_copy["verification"] = result
            new_hypotheses.append(hyp_copy)
        incident.hypotheses = new_hypotheses


        try:
            db.commit()
            logger.info(f"Saved hypothesis {hypothesis_id} verification verdict: {verdict}")
            return result
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update verification database: {e}")
            raise ValueError(f"Database write failed: {e}")
