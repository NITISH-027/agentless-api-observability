import re
import os
import uuid
import json
import time
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.models.incident import Incident, InvestigationStatus
from app.services.github.workspace import WorkspaceManager
from app.services.reproduction.sandbox import SandboxExecutor
from app.services.analysis.llm_provider import BaseLLMProvider

logger = logging.getLogger("app.services.patch.patch_generator")

# ==========================================
# Pydantic Schema for LLM Patch Generation
# ==========================================
class PatchModel(BaseModel):
    files_to_modify: List[str] = Field(..., description="List of source files in repository modified by the patch")
    patch_diff: str = Field(..., description="Unified diff patch code string")
    explanation: str = Field(..., description="Human-readable explanation of why this patch resolves the bug safely")
    root_cause_addressed: str = Field(..., description="Root cause description addressed by the changes")
    tests_added_or_modified: List[str] = Field(default_factory=list, description="List of test files modified/added")
    risk_notes: str = Field(..., description="Potential side effects or risks of this patch")

# ==========================================
# Safety Check Helpers
# ==========================================
def contains_secrets(diff: str) -> bool:
    """
    Checks if the diff contains credentials or high-entropy secrets using regular expressions.
    """
    secret_patterns = [
        r'(AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY|AWS_KEY|AWS_SECRET)\s*=\s*["\'][A-Za-z0-9/+=]{16,}["\']',
        r'(api_key|client_secret|db_password|password|token)\s*=\s*["\'][A-Za-z0-9_\-\.\+=]{8,}["\']',
        r'xox[baprs]-[0-9]{12}-[0-9]{12}-[a-zA-Z0-9]{24}'
    ]
    for pattern in secret_patterns:
        if re.search(pattern, diff, re.IGNORECASE):
            return True
    return False

def contains_suspicious_files(files: List[str]) -> bool:
    """
    Blocks patches that modify sensitive config/environment files.
    """
    suspicious_names = {
        ".env", ".env.example", "dockerfile", "docker-compose.yml",
        "requirements.txt", "pyproject.toml"
    }
    for file_path in files:
        basename = os.path.basename(file_path).lower()
        if basename in suspicious_names:
            return True
    return False

# ==========================================
# Prompt Construction
# ==========================================
def build_patch_prompt(
    incident: Incident,
    hypothesis: Dict[str, Any],
    traceback_analysis: Dict[str, Any],
    reproducer_code: str
) -> str:
    prompt = f"""You are generating a final production-grade patch (unified git diff) to fix a validated API failure.

[INCIDENT DETAILS]
Exception: {incident.error_type} - {incident.error_message}
Request Method: {incident.request_method}
Request Path: {incident.request_path}
Request Body: {json.dumps(incident.request_body or {})}

[VALIDATED HYPOTHESIS]
Title: {hypothesis.get('title')}
Category: {hypothesis.get('category')}
Description: {hypothesis.get('description')}
Evidence: {json.dumps(hypothesis.get('supporting_evidence', []))}

[PYTEST REPRODUCER]
```python
{reproducer_code}
```
"""

    prompt += "\n[RELEVANT REPOSITORY SOURCES]\n"
    for frame in traceback_analysis.get("frames", []):
        if frame.get("mapped"):
            prompt += f"File: {frame.get('repo_path')}\n"
            prompt += f"Scope: Class '{frame.get('containing_class')}', Function '{frame.get('containing_function')}'\n"
            prompt += "Code Lines:\n"
            for line in frame.get("context", []):
                prompt += f"  {line.get('line_number')}: {line.get('content')}\n"
            prompt += "---------------------------------------\n"

    prompt += """
[INSTRUCTIONS]
1. Generate the SMALLEST safe patch possible to resolve the bug.
2. Modify ONLY the necessary files. Do NOT perform unrelated refactoring.
3. Ensure no secrets (API keys, credentials) are introduced.
4. Explain every modification.
5. Provide the output in a clean structured JSON format.
"""
    return prompt

# ==========================================
# Patch Engine Class
# ==========================================
class PatchGenerator:
    def __init__(self, workspace_manager: Optional[WorkspaceManager] = None):
        self.wm = workspace_manager or WorkspaceManager()

    async def generate_and_verify_patch(
        self,
        db: Session,
        incident_id: str,
        hypothesis_id: str,
        token: str,
        provider: BaseLLMProvider,
        max_retries: int = 3,
        timeout: float = 15.0
    ) -> Dict[str, Any]:
        logger.info(f"Initiating patch generation for incident {incident_id}, hypothesis {hypothesis_id}")
        
        # 1. Fetch incident record
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")

        # 2. Check if the specified hypothesis was validated
        verifications = incident.verification_results or {}
        validated_hyp = verifications.get(hypothesis_id)
        if not validated_hyp or validated_hyp.get("verdict") != "VALIDATED":
            raise ValueError(f"Hypothesis {hypothesis_id} has not been validated. Verification verdict: {validated_hyp.get('verdict') if validated_hyp else 'None'}")

        # Find the matching hypothesis in hypotheses array
        hypothesis_details = {}
        for hyp in (incident.hypotheses or []):
            if hyp.get("id") == hypothesis_id:
                hypothesis_details = hyp
                break
                
        # 3. Read reproducer test code from baseline reproduction
        baseline = incident.reproduction_result
        if not baseline or not baseline.get("reproduced"):
            raise ValueError("Baseline reproduction results are missing or failed. Cannot verify patch.")
            
        baseline_ws_id = baseline.get("workspace_id") or "ws_test"
        test_relative_path = baseline.get("test_path", "reproduce_test.py")
        
        try:
            reproducer_code = self.wm.read_file(baseline_ws_id, test_relative_path)
        except Exception as e:
            logger.warning(f"Could not read reproducer from baseline workspace: {e}")
            reproducer_code = ""

        # 4. Generate patch using LLM
        prompt = build_patch_prompt(incident, hypothesis_details, incident.traceback_analysis, reproducer_code)
        
        system_instruction = (
            "You are a production patch generation engineer. Your output must strictly match the following JSON schema:\n"
            "{\n"
            '  "files_to_modify": ["src/service.py"],\n'
            '  "patch_diff": "diff --git a/src/service.py b/src/service.py\\n...",\n' # Must be valid unified diff format
            '  "explanation": "Detailed explanation of changes.",\n'
            '  "root_cause_addressed": "Negative values passed to calculate_total.",\n'
            '  "tests_added_or_modified": [],\n'
            '  "risk_notes": "None"\n'
            "}\n"
            "Output only valid JSON."
        )

        retries = 0
        validation_error = ""
        patch_model: Optional[PatchModel] = None
        
        while retries < max_retries:
            try:
                current_sys = system_instruction
                if validation_error:
                    current_sys += f"\nYour previous output failed validation: {validation_error}. Please output correct JSON."
                    
                raw_response = await provider.complete(prompt, current_sys)
                
                # Sanitize markdown wrapper
                json_str = raw_response.strip()
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0].strip()
                    
                data = json.loads(json_str)
                patch_model = PatchModel.model_validate(data)
                break
            except Exception as e:
                retries += 1
                validation_error = str(e)
                logger.warning(f"Patch generation attempt {retries} failed: {e}")
                
        if not patch_model:
            raise ValueError(f"Failed to generate structured patch after {max_retries} attempts: {validation_error}")

        # 5. Programmatic Safety Validations
        patch_diff = patch_model.patch_diff
        modified_files = patch_model.files_to_modify
        
        # Security: Secret detector
        if contains_secrets(patch_diff):
            return self._save_failure(db, incident, "PATCH_VERIFICATION_FAILED: Secrets or API keys detected inside generated patch content.")
            
        # Security: Suspicious config file checker
        if contains_suspicious_files(modified_files):
            return self._save_failure(db, incident, "PATCH_VERIFICATION_FAILED: Modification of suspicious/critical system files blocked.")

        # 6. Apply patch and test inside clean sandbox
        owner = incident.github_owner
        repo = incident.github_repo
        commit_sha = incident.github_commit_sha
        branch = incident.github_branch
        
        verify_ws_id = None
        start_time = time.time()
        
        try:
            # Clone clean repository snapshot
            verify_ws_id = self.wm.clone_repository(token, owner, repo, commit_sha, branch)
            
            # Write reproducer
            test_file_path = self.wm._get_repo_path(verify_ws_id) / test_relative_path
            with open(test_file_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(reproducer_code)
                
            # Apply patch
            logger.info("Applying patch to verification workspace...")
            self.wm.apply_patch(verify_ws_id, patch_diff)
        except Exception as e:
            logger.error(f"Patch failed to apply cleanly: {e}")
            if verify_ws_id:
                self.wm.delete_workspace(verify_ws_id)
            return self._save_failure(db, incident, f"PATCH_VERIFICATION_FAILED: Patch failed to apply cleanly: {e}")

        # Run sandbox Pytest reproducer
        try:
            from app.core.config import get_settings
            app_settings = get_settings()
            allow_fallback = os.environ.get("ALLOW_LOCAL_SANDBOX_FALLBACK", "true").lower() == "true"
            
            executor = SandboxExecutor(
                sandbox_image=app_settings.SANDBOX_IMAGE,
                allow_local_fallback=allow_fallback
            )
            
            run_res = executor.run_test(
                workspace_path=self.wm._get_workspace_path(verify_ws_id),
                test_relative_path=test_relative_path,
                timeout=timeout
            )
        except Exception as e:
            logger.error(f"Sandbox runner crashed during patch verify: {e}")
            self.wm.delete_workspace(verify_ws_id)
            return self._save_failure(db, incident, f"PATCH_VERIFICATION_FAILED: Sandbox crashed: {e}")

        # Cleanup verification workspace
        self.wm.delete_workspace(verify_ws_id)
        
        exit_code = run_res.get("exit_code", -1)
        
        # Evaluate outcome
        if exit_code == 0:
            # Fix is verified and accepted!
            result = {
                "status": "ACCEPTED",
                "files_to_modify": patch_model.files_to_modify,
                "patch_diff": patch_model.patch_diff,
                "explanation": patch_model.explanation,
                "root_cause_addressed": patch_model.root_cause_addressed,
                "tests_added_or_modified": patch_model.tests_added_or_modified,
                "risk_notes": patch_model.risk_notes,
                "verification_logs": run_res.get("stdout", "") + "\n" + run_res.get("stderr", ""),
                "duration_ms": int((time.time() - start_time) * 1000)
            }
            incident.patch_result = result
            incident.status = InvestigationStatus.FIXED
            db.commit()
            logger.info(f"Patch successfully validated and accepted for incident {incident_id}")
            return result
        else:
            # Reproducer test still failed!
            return self._save_failure(
                db, incident,
                f"PATCH_VERIFICATION_FAILED: Patch was applied but reproducer test execution failed with exit code {exit_code}."
            )

    def _save_failure(self, db: Session, incident: Incident, reason: str) -> Dict[str, Any]:
        result = {
            "status": "PATCH_VERIFICATION_FAILED",
            "reason": reason,
            "failed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        incident.patch_result = result
        incident.status = InvestigationStatus.FAILED
        try:
            db.commit()
            logger.warning(f"Patch verification failed: {reason}")
            return result
        except Exception as e:
            db.rollback()
            raise ValueError(f"Database write failed: {e}")
