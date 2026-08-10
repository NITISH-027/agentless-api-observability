import subprocess
import time
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("app.services.reproduction.sandbox")

class SandboxExecutor:
    """
    Executes Pytest reproducer test files inside an isolated environment.
    Tries to launch Docker if available; otherwise falls back to local subprocess
    execution ONLY if allow_local_fallback is enabled (e.g. in test suites).
    """
    def __init__(self, sandbox_image: str = "python:3.10-slim", allow_local_fallback: bool = False):
        self.sandbox_image = sandbox_image
        self.allow_local_fallback = allow_local_fallback

    def _check_docker_available(self) -> bool:
        try:
            # Check if docker command is available
            res = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            return res.returncode == 0
        except Exception:
            return False

    def run_test(
        self,
        workspace_path: Path,
        test_relative_path: str,
        timeout: float = 15.0
    ) -> Dict[str, Any]:
        repo_dir = workspace_path / "repository"
        abs_repo_path = str(repo_dir.resolve())
        
        has_docker = self._check_docker_available()
        start_time = time.time()
        
        output_limit = 50000  # Cap stdout/stderr to 50KB to protect host memory
        
        if has_docker:
            logger.info(f"Docker found. Running tests inside image '{self.sandbox_image}'")
            
            # Auto-install requirements.txt if present inside the repository
            requirements_file = repo_dir / "requirements.txt"
            pip_cmd = ""
            if requirements_file.exists():
                pip_cmd = "pip install -q -r requirements.txt && "
                
            # Docker run mounting absolute host path to /app in container
            docker_cmd = [
                "docker", "run", "--rm",
                "-v", f"{abs_repo_path}:/app",
                "-w", "/app",
                self.sandbox_image,
                "sh", "-c", f"{pip_cmd}pytest {test_relative_path}"
            ]
            
            try:
                proc = subprocess.run(
                    docker_cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    errors="ignore"
                )
                duration = int((time.time() - start_time) * 1000)
                return {
                    "success": True,
                    "exit_code": proc.returncode,
                    "stdout": proc.stdout[:output_limit],
                    "stderr": proc.stderr[:output_limit],
                    "duration_ms": duration
                }
            except subprocess.TimeoutExpired as e:
                logger.warning(f"Docker sandbox timed out after {timeout} seconds")
                stdout = (e.stdout or "")[:output_limit]
                stderr = (e.stderr or "")[:output_limit]
                return {
                    "success": False,
                    "exit_code": -1,
                    "stdout": stdout,
                    "stderr": stderr + f"\n[TIMEOUT] Execution exceeded {timeout} seconds limit",
                    "duration_ms": int(timeout * 1000),
                    "reason": "Timeout expired"
                }
            except Exception as e:
                logger.error(f"Failed to execute Docker container sandbox: {e}")
                return {
                    "success": False,
                    "exit_code": -1,
                    "stdout": "",
                    "stderr": str(e),
                    "duration_ms": int((time.time() - start_time) * 1000),
                    "reason": f"Docker run failed: {e}"
                }
        else:
            if not self.allow_local_fallback:
                logger.warning("Docker daemon is missing and local fallback execution is disabled.")
                return {
                    "success": False,
                    "exit_code": -1,
                    "stdout": "",
                    "stderr": "Docker daemon not found on host system.",
                    "duration_ms": 0,
                    "reason": "Docker sandbox not available"
                }
                
            logger.info("Docker daemon missing. Executing locally via subprocess (Local Fallback enabled).")
            
            # Resolve local virtual env pytest if available
            pytest_bin = "pytest"
            venv_pytest = Path(__file__).resolve().parent.parent.parent.parent / ".venv" / "Scripts" / "pytest.exe"
            if venv_pytest.exists():
                pytest_bin = str(venv_pytest)
                
            cmd = [pytest_bin, test_relative_path]
            
            try:
                proc = subprocess.run(
                    cmd,
                    cwd=abs_repo_path,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    errors="ignore"
                )
                duration = int((time.time() - start_time) * 1000)
                return {
                    "success": True,
                    "exit_code": proc.returncode,
                    "stdout": proc.stdout[:output_limit],
                    "stderr": proc.stderr[:output_limit],
                    "duration_ms": duration
                }
            except subprocess.TimeoutExpired as e:
                logger.warning(f"Local subprocess timed out after {timeout} seconds")
                stdout = (e.stdout or "")[:output_limit]
                stderr = (e.stderr or "")[:output_limit]
                return {
                    "success": False,
                    "exit_code": -1,
                    "stdout": stdout,
                    "stderr": stderr + f"\n[TIMEOUT] Local execution exceeded {timeout} seconds limit",
                    "duration_ms": int(timeout * 1000),
                    "reason": "Timeout expired"
                }
            except Exception as e:
                logger.error(f"Local subprocess launch failure: {e}")
                return {
                    "success": False,
                    "exit_code": -1,
                    "stdout": "",
                    "stderr": str(e),
                    "duration_ms": int((time.time() - start_time) * 1000),
                    "reason": f"Local execution failed: {e}"
                }
