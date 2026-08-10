import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.incident import Incident, InvestigationStatus
from app.core.config import get_settings
from app.services.github.workspace import WorkspaceManager
from app.services.reproduction.reproducer_generator import ReproducerGenerator
from app.services.reproduction.sandbox import SandboxExecutor
from app.services.analysis.mapper import TracebackMapper
from app.services.analysis.llm_provider import BaseLLMProvider

logger = logging.getLogger("app.services.reproduction.manager")

class ReproductionManager:
    """
    Orchestrates the lifecycle of failure reproduction.
    Generates a targeted test script, runs it in the sandbox environment,
    inspects outputs to verify the exception, and logs results.
    """
    def __init__(self, workspace_manager: Optional[WorkspaceManager] = None):
        self.wm = workspace_manager or WorkspaceManager()

    async def reproduce_incident(
        self,
        db: Session,
        incident_id: str,
        workspace_id: str,
        provider: BaseLLMProvider,
        token: Optional[str] = None,
        timeout: float = 15.0
    ) -> Dict[str, Any]:
        logger.info(f"Initiating failure reproduction for incident {incident_id} in workspace {workspace_id}")
        
        # 1. Retrieve Incident
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")
            
        # 2. Retrieve traceback analysis (run mapping if missing)
        analysis = incident.traceback_analysis
        if not analysis:
            logger.info("Traceback analysis missing. Running mapping analysis first...")
            mapper = TracebackMapper(self.wm)
            analysis = mapper.analyze_incident_traceback(db, incident_id, workspace_id, token=token)

        # Ensure repository exists on disk
        repo_dir = self.wm._get_repo_path(workspace_id)
        ws_dir = self.wm._get_workspace_path(workspace_id)
        if not repo_dir.exists():
            logger.info(f"Workspace repository {workspace_id} does not exist during reproduction. Cloning on-demand...")
            if not incident.github_owner or not incident.github_repo:
                raise ValueError("Repository details not associated with this incident.")
            
            settings = get_settings()
            active_token = token or settings.GITHUB_TOKEN
            if not active_token or active_token == "dummy_github_token":
                raise ValueError("GitHub credentials not configured for sandbox reproduction.")
                
            self.wm.clone_repository(
                token=active_token,
                owner=incident.github_owner,
                repo=incident.github_repo,
                commit_sha=incident.github_commit_sha or "main",
                branch=incident.github_branch or "main",
                workspace_id=workspace_id
            )
            # Re-resolve directories
            repo_dir = self.wm._get_repo_path(workspace_id)
            ws_dir = self.wm._get_workspace_path(workspace_id)

        # 3. Generate Pytest reproducer code
        generator = ReproducerGenerator()
        try:
            test_code = await generator.generate_reproducer(incident, analysis, provider)
        except Exception as e:
            logger.error(f"Failed to generate reproducer test code: {e}")
            result = {
                "reproduced": False,
                "exit_code": -1,
                "duration_ms": 0,
                "stdout": "",
                "stderr": f"Failed to generate reproducer: {e}",
                "test_path": "reproduce_test.py",
                "reason": "REPRODUCTION_FAILED: generated test invalid"
            }
            incident.reproduction_result = result
            incident.status = InvestigationStatus.FAILED
            db.commit()
            return result

        # 4. Write reproducer test code to workspace repository
        test_relative_path = "reproduce_test.py"
        test_file_path = repo_dir / test_relative_path
        
        try:
            with open(test_file_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(test_code)
            logger.info(f"Written reproducer test to {test_file_path}")
        except Exception as e:
            logger.error(f"Failed to write reproducer test file: {e}")
            raise ValueError(f"Workspace file write failed: {e}")

        # 5. Execute sandbox runner
        settings = get_settings()
        # Allow local fallback inside tests/dev environment
        allow_fallback = os.environ.get("ALLOW_LOCAL_SANDBOX_FALLBACK", "true").lower() == "true"
        
        executor = SandboxExecutor(
            sandbox_image=settings.SANDBOX_IMAGE,
            allow_local_fallback=allow_fallback
        )
        
        run_res = executor.run_test(
            workspace_path=ws_dir,
            test_relative_path=test_relative_path,
            timeout=timeout
        )
        
        # 6. Verify reproduction assertions
        reproduced = False
        reason = None
        
        exit_code = run_res.get("exit_code", -1)
        stdout = run_res.get("stdout", "")
        stderr = run_res.get("stderr", "")
        duration = run_res.get("duration_ms", 0)
        
        # We parse the outputs to check if the target exception was raised.
        # Since we instructed pytest to bubble up the exception, the exit code should be non-zero (failed).
        if exit_code != 0:
            combined_output = stdout + "\n" + stderr
            expected_exc = incident.error_type
            
            # Check if exception type or message is in the pytest output log
            if expected_exc in combined_output:
                reproduced = True
                logger.info(f"Success! Exception '{expected_exc}' was verified in the test logs.")
            else:
                reproduced = False
                reason = "REPRODUCTION_FAILED: test failed but expected exception type was missing from logs"
        else:
            # If the test passed, it means no unhandled exception bubbled up.
            reproduced = False
            reason = "REPRODUCTION_FAILED: test execution succeeded without raising target exception"
            
        if not run_res.get("success", True):
            # Sandbox runner itself reported failure (e.g. timeout or docker not present)
            reproduced = False
            reason = f"REPRODUCTION_FAILED: {run_res.get('reason', 'execution failure')}"

        # 7. Construct final reproduction result
        result = {
            "reproduced": reproduced,
            "exception_type": incident.error_type if reproduced else None,
            "exception_message": incident.error_message if reproduced else None,
            "exit_code": exit_code,
            "duration_ms": duration,
            "stdout": stdout,
            "stderr": stderr,
            "test_path": test_relative_path,
            "workspace_id": workspace_id,
            "reason": reason
        }

        # 8. Update database incident record
        try:
            incident.reproduction_result = result
            if reproduced:
                incident.status = InvestigationStatus.REPRODUCING
            else:
                incident.status = InvestigationStatus.FAILED
                
            db.commit()
            logger.info(f"Updated incident {incident_id} with reproduction result. Status: {incident.status}")
            return result
        except Exception as e:
            db.rollback()
            logger.error(f"Database write failure for reproduction results: {e}")
            raise ValueError(f"Database write failed: {e}")
