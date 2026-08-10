import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.services.github.workspace import WorkspaceManager
from app.services.analysis.traceback_parser import parse_traceback_string
from app.services.analysis.ast_analyzer import analyze_source_ast

logger = logging.getLogger("app.services.analysis.mapper")

def resolve_repo_path(
    traceback_path: str,
    repo_files: List[str],
    function_name: Optional[str] = None,
    workspace_manager: Optional[Any] = None,
    workspace_id: Optional[str] = None
) -> Optional[str]:
    """
    Finds the best matching repository file corresponding to a production stack trace path.
    Supports suffix matching, basename matching, and function signature lookup fallbacks.
    """
    norm_traceback = traceback_path.replace("\\", "/").strip("/")
    tb_filename = Path(norm_traceback).name
    
    longest_match = None
    longest_match_len = -1
    
    # 1. Direct or reverse suffix match
    for repo_file in repo_files:
        norm_repo = repo_file.replace("\\", "/").strip("/")
        if norm_traceback.endswith(norm_repo) or norm_repo.endswith(norm_traceback):
            if len(norm_repo) > longest_match_len:
                longest_match = repo_file
                longest_match_len = len(norm_repo)
                
    if longest_match:
        return longest_match

    # 2. Exact filename match
    for repo_file in repo_files:
        norm_repo = repo_file.replace("\\", "/").strip("/")
        if Path(norm_repo).name == tb_filename:
            return repo_file

    # 3. Fallback: Search for function definition in repo files
    if function_name and workspace_manager and workspace_id:
        target_def = f"def {function_name}"
        for repo_file in repo_files:
            try:
                content = workspace_manager.read_file(workspace_id, repo_file)
                if target_def in content:
                    return repo_file
            except Exception:
                pass
                
    return None

def get_line_context(content: str, target_line: int, context_size: int = 5) -> List[Dict[str, Any]]:
    """
    Retrieves surrounding lines of context for a given target line (1-indexed).
    """
    lines = content.splitlines()
    total = len(lines)
    
    # Ensure line bounds
    start = max(1, target_line - context_size)
    end = min(total, target_line + context_size)
    
    context = []
    for line_num in range(start, end + 1):
        context.append({
            "line_number": line_num,
            "content": lines[line_num - 1],
            "is_target": line_num == target_line
        })
    return context

class TracebackMapper:
    """
    Orchestrates stack trace parsing and associates trace frames with actual
    repository source file locations, scopes, and context evidence.
    """
    def __init__(self, workspace_manager: Optional[WorkspaceManager] = None):
        self.wm = workspace_manager or WorkspaceManager()

    def analyze_incident_traceback(self, db: Session, incident_id: str, workspace_id: str, token: Optional[str] = None) -> Dict[str, Any]:
        logger.info(f"Analyzing traceback for incident {incident_id} using workspace {workspace_id}")
        
        # 1. Fetch incident record
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")
            
        traceback_str = incident.error_stack_trace
        if not traceback_str:
            raise ValueError(f"Incident {incident_id} does not contain an error stack trace")
            
        # 2. Parse frames and exception info
        parsed_frames, exc_type, exc_msg = parse_traceback_string(traceback_str)
        
        # 3. Ensure workspace files exist on disk, clone on-demand if missing
        repo_path = self.wm._get_repo_path(workspace_id)
        if not repo_path.exists():
            logger.info(f"Workspace repository {workspace_id} does not exist. Attempting on-demand clone...")
            if not incident.github_owner or not incident.github_repo:
                raise ValueError(f"Workspace {workspace_id} does not exist and incident has no associated repository.")
            
            # Resolve GITHUB_TOKEN dynamically
            from app.core.config import get_settings
            settings = get_settings()
            
            active_token = token
            if not active_token:
                active_token = settings.GITHUB_TOKEN
                
            if not active_token or active_token == "dummy_github_token":
                raise ValueError("Workspace repository missing and GitHub token credentials are not configured.")
                
            try:
                self.wm.clone_repository(
                    token=active_token,
                    owner=incident.github_owner,
                    repo=incident.github_repo,
                    commit_sha=incident.github_commit_sha or "main",
                    branch=incident.github_branch or "main",
                    workspace_id=workspace_id
                )
                
                # Check resolved commit SHA in metadata to sync database row
                meta_file = self.wm._get_workspace_path(workspace_id) / "metadata.json"
                if meta_file.exists():
                    import json
                    with open(meta_file, "r") as f:
                        meta = json.load(f)
                        resolved_sha = meta.get("commit_sha")
                        if resolved_sha and resolved_sha != incident.github_commit_sha:
                            logger.info(f"Syncing actual commit SHA to database: {resolved_sha}")
                            incident.github_commit_sha = resolved_sha
                            db.commit()
            except Exception as clone_err:
                logger.error(f"On-demand workspace cloning failed: {clone_err}")
                raise ValueError(f"Workspace repository missing and on-demand clone failed: {clone_err}")

        # 4. Retrieve workspace file listing
        try:
            repo_files = self.wm.list_files(workspace_id)
        except Exception as e:
            logger.error(f"Failed to list files in workspace {workspace_id}: {e}")
            raise ValueError(f"Invalid workspace {workspace_id} or repository missing: {e}")
            
        # 4. Map frames to workspace files
        mapped_frames = []
        files_in_traceback = []
        
        for frame in parsed_frames:
            raw_path = frame["file_path"]
            line_num = frame["line_number"]
            func_name = frame["function_name"]
            repo_path = resolve_repo_path(
                raw_path,
                repo_files,
                function_name=func_name,
                workspace_manager=self.wm,
                workspace_id=workspace_id
            )
            
            frame_analysis = {
                "raw_file_path": raw_path,
                "line_number": line_num,
                "function_name": func_name,
                "code_line": frame["code_line"],
                "mapped": False,
                "repo_path": None,
                "containing_class": None,
                "containing_function": None,
                "context": [],
                "imports": [],
                "calls": []
            }
            
            if repo_path:
                frame_analysis["mapped"] = True
                frame_analysis["repo_path"] = repo_path
                
                if repo_path not in files_in_traceback:
                    files_in_traceback.append(repo_path)
                    
                # Read file contents and fetch context
                try:
                    file_content = self.wm.read_file(workspace_id, repo_path)
                    frame_analysis["context"] = get_line_context(file_content, line_num)
                    
                    # Run AST analysis
                    ast_data = analyze_source_ast(file_content)
                    frame_analysis["imports"] = ast_data["imports"]
                    
                    # Identify containing class/function from target line
                    for cls in ast_data["classes"]:
                        if cls["start_line"] <= line_num <= cls["end_line"]:
                            frame_analysis["containing_class"] = cls["name"]
                            break
                            
                    for func in ast_data["functions"]:
                        if func["start_line"] <= line_num <= func["end_line"]:
                            frame_analysis["containing_function"] = func["name"]
                            frame_analysis["calls"] = func["calls"]
                            break
                except Exception as e:
                    logger.warning(f"Failed to complete code context lookup for {repo_path}: {e}")
                    
            mapped_frames.append(frame_analysis)
            
        # 5. Build static call graph links
        # Trace relationship: Frame[i] -> Frame[i+1]
        call_graph = []
        for i in range(len(mapped_frames) - 1):
            parent = mapped_frames[i]
            child = mapped_frames[i + 1]
            
            relation = {
                "parent": {
                    "file": parent["repo_path"] or parent["raw_file_path"],
                    "function": parent["function_name"],
                    "line": parent["line_number"]
                },
                "child": {
                    "file": child["repo_path"] or child["raw_file_path"],
                    "function": child["function_name"],
                    "line": child["line_number"]
                },
                "relationship": "uncertain"
            }
            
            # Check if parent AST contains the child function call token
            child_func = child["function_name"]
            if parent["mapped"] and child_func in parent["calls"]:
                relation["relationship"] = "confirmed_static"
                
            call_graph.append(relation)
            
        # 6. Identify final failure point
        final_failure = None
        # Traverse backward to find the last mapped frame
        for frame in reversed(mapped_frames):
            if frame["mapped"]:
                final_failure = {
                    "file": frame["repo_path"],
                    "line": frame["line_number"],
                    "function": frame["function_name"],
                    "error_type": exc_type,
                    "error_message": exc_msg
                }
                break
                
        # If no frame could be mapped, default to last parsed frame details
        if not final_failure and mapped_frames:
            last = mapped_frames[-1]
            final_failure = {
                "file": last["raw_file_path"],
                "line": last["line_number"],
                "function": last["function_name"],
                "error_type": exc_type,
                "error_message": exc_msg
            }

        # 7. Compile structured evidence payload
        evidence = {
            "incident_id": incident_id,
            "workspace_id": workspace_id,
            "exception_type": exc_type,
            "exception_message": exc_msg,
            "files_in_traceback": files_in_traceback,
            "final_failure": final_failure,
            "frames": mapped_frames,
            "call_graph": call_graph
        }
        
        # Save to database
        try:
            incident.traceback_analysis = evidence
            db.commit()
            logger.info(f"Successfully saved traceback evidence to database for incident {incident_id}")
            return evidence
        except Exception as e:
            db.rollback()
            logger.error(f"Database save error for traceback evidence: {e}")
            raise ValueError(f"Database write failed: {e}")
