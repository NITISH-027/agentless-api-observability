import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.models.incident import Incident, InvestigationStatus
from app.services.analysis.traceback_parser import parse_traceback_string
from app.services.analysis.ast_analyzer import analyze_source_ast
from app.services.analysis.mapper import TracebackMapper, resolve_repo_path, get_line_context
from app.services.github.workspace import WorkspaceManager

# ==========================================
# Unit Tests for Traceback Parser
# ==========================================
def test_traceback_parser_normal():
    tb_str = """
Traceback (most recent call last):
  File "/app/src/orders/router.py", line 31, in create_order
    return service.create_order(data)
  File "/app/src/orders/service.py", line 87, in create_order
    total = calculate_total(data)
ValueError: invalid quantity
    """
    frames, exc_type, exc_msg = parse_traceback_string(tb_str)
    
    assert exc_type == "ValueError"
    assert exc_msg == "invalid quantity"
    assert len(frames) == 2
    
    assert frames[0]["file_path"] == "/app/src/orders/router.py"
    assert frames[0]["line_number"] == 31
    assert frames[0]["function_name"] == "create_order"
    assert frames[0]["code_line"] == "return service.create_order(data)"
    
    assert frames[1]["file_path"] == "/app/src/orders/service.py"
    assert frames[1]["line_number"] == 87
    assert frames[1]["function_name"] == "create_order"
    assert frames[1]["code_line"] == "total = calculate_total(data)"


# ==========================================
# Unit Tests for AST Analyzer
# ==========================================
def test_ast_analyzer_valid():
    source = """
import os
from math import log

class Calculator:
    def add(self, a, b):
        result = a + b
        log(result)
        return result

def run_calc():
    c = Calculator()
    c.add(1, 2)
"""
    ast_data = analyze_source_ast(source)
    
    assert "os" in ast_data["imports"]
    assert "math.log" in ast_data["imports"]
    
    # Assert Calculator class scope
    assert len(ast_data["classes"]) == 1
    assert ast_data["classes"][0]["name"] == "Calculator"
    assert ast_data["classes"][0]["start_line"] == 5
    
    # Assert function boundaries and calls
    assert len(ast_data["functions"]) == 2
    
    # Calculator.add
    add_func = [f for f in ast_data["functions"] if f["name"] == "add"][0]
    assert add_func["class_name"] == "Calculator"
    assert "log" in add_func["calls"]
    
    # run_calc
    run_func = [f for f in ast_data["functions"] if f["name"] == "run_calc"][0]
    assert run_func["class_name"] is None
    assert "Calculator" in run_func["calls"]

def test_ast_analyzer_syntax_error():
    # Malformed Python code missing a colon
    bad_source = "def run()\n    print(1)"
    ast_data = analyze_source_ast(bad_source)
    
    assert "error" in ast_data
    assert ast_data["classes"] == []
    assert ast_data["functions"] == []


# ==========================================
# Unit Tests for Path Normalization
# ==========================================
def test_resolve_repo_path():
    repo_files = [
        "src/orders/service.py",
        "src/orders/router.py",
        "utils/helper.py"
    ]
    
    # Matching production prefix path
    match1 = resolve_repo_path("/production/app/src/orders/service.py", repo_files)
    assert match1 == "src/orders/service.py"
    
    # Suffix match only
    match2 = resolve_repo_path("app/utils/helper.py", repo_files)
    assert match2 == "utils/helper.py"
    
    # Mismatch returns None
    match3 = resolve_repo_path("/production/app/lib/external.py", repo_files)
    assert match3 is None


def test_get_line_context():
    content = "\n".join([f"Line {i}" for i in range(1, 20)])
    context = get_line_context(content, target_line=10, context_size=3)
    
    assert len(context) == 7  # 10-3 to 10+3
    assert context[0]["line_number"] == 7
    assert context[3]["line_number"] == 10
    assert context[3]["is_target"] is True
    assert context[3]["content"] == "Line 10"


# ==========================================
# Path Traversal Protection
# ==========================================
def test_path_traversal_escape(tmp_path):
    wm = WorkspaceManager(base_path=str(tmp_path))
    workspace_id = "ws_test"
    ws_dir = tmp_path / workspace_id
    ws_dir.mkdir()
    (ws_dir / "repository").mkdir()
    
    with pytest.raises(ValueError) as exc_info:
        wm.read_file(workspace_id, "../../../etc/passwd")
    assert "path traversal violation" in str(exc_info.value).lower()


# ==========================================
# Traceback Mapping Integration tests
# ==========================================
def test_traceback_mapper_integration(tmp_path, db_session):
    # Setup mock workspace files in filesystem
    wm = WorkspaceManager(base_path=str(tmp_path))
    workspace_id = "ws_mock_analysis"
    ws_dir = tmp_path / workspace_id
    ws_dir.mkdir()
    
    repo_dir = ws_dir / "repository"
    repo_dir.mkdir()
    
    # 1. Create repo files
    router_code = """
from src.service import OrderService
def route_call():
    srv = OrderService()
    srv.create_order()
"""
    service_code = """
class OrderService:
    def create_order(self):
        self.process_order()

    def process_order(self):
        raise ValueError("quantity negative")
"""
    # Write files
    (repo_dir / "src").mkdir()
    (repo_dir / "src" / "router.py").write_text(router_code, encoding="utf-8")
    (repo_dir / "src" / "service.py").write_text(service_code, encoding="utf-8")
    
    # Create metadata.json so wm lists files correctly
    import json
    metadata = {
        "workspace_id": workspace_id,
        "owner": "mock_owner",
        "repository": "mock_repo",
        "commit_sha": "mock_sha"
    }
    with open(ws_dir / "metadata.json", "w") as f:
        json.dump(metadata, f)

    # 2. Setup mock incident with traceback referencing production paths
    traceback = """
Traceback (most recent call last):
  File "/production/app/src/router.py", line 5, in route_call
    srv.create_order()
  File "/production/app/src/service.py", line 4, in create_order
    self.process_order()
  File "/production/app/src/service.py", line 7, in process_order
    raise ValueError("quantity negative")
ValueError: quantity negative
"""
    from datetime import datetime, timezone
    incident_id = "inc_analysis_test"
    db_incident = Incident(
        id=incident_id,
        fingerprint="fp_analysis",
        service="order-api",
        environment="production",
        timestamp=datetime.now(timezone.utc),
        ingested_at=datetime.now(timezone.utc),
        status=InvestigationStatus.RECEIVED,
        request_method="POST",
        request_path="/api/orders",
        response_status_code=500,
        error_type="ValueError",
        error_message="quantity negative",
        error_stack_trace=traceback
    )
    db_session.add(db_incident)
    db_session.commit()

    # 3. Execute mapping analysis
    mapper = TracebackMapper(workspace_manager=wm)
    evidence = mapper.analyze_incident_traceback(db_session, incident_id, workspace_id)
    
    # 4. Assert mapping outcomes
    assert evidence["exception_type"] == "ValueError"
    assert "src/router.py" in evidence["files_in_traceback"]
    assert "src/service.py" in evidence["files_in_traceback"]
    
    # Final failure point details
    assert evidence["final_failure"]["file"] == "src/service.py"
    assert evidence["final_failure"]["line"] == 7
    assert evidence["final_failure"]["function"] == "process_order"
    
    # Assert AST function scope resolutions
    frames = evidence["frames"]
    assert len(frames) == 3
    
    # Frame 0: router.py
    assert frames[0]["mapped"] is True
    assert frames[0]["repo_path"] == "src/router.py"
    assert frames[0]["containing_function"] == "route_call"
    
    # Frame 1: service.py (create_order method inside class OrderService)
    assert frames[1]["mapped"] is True
    assert frames[1]["repo_path"] == "src/service.py"
    assert frames[1]["containing_class"] == "OrderService"
    assert frames[1]["containing_function"] == "create_order"
    
    # Assert Call Graph status linkages
    call_graph = evidence["call_graph"]
    assert len(call_graph) == 2
    
    # Link 0: route_call -> create_order (Parent route_call calls 'create_order') -> confirmed_static
    assert call_graph[0]["relationship"] == "confirmed_static"
    # Link 1: create_order -> process_order (Parent create_order calls 'process_order') -> confirmed_static
    assert call_graph[1]["relationship"] == "confirmed_static"

# ==========================================
# Route API test
# ==========================================
@patch("app.services.analysis.mapper.TracebackMapper.analyze_incident_traceback")
def test_analyze_endpoint(mock_analyze, client: TestClient):
    mock_analyze.return_value = {"status": "analyzed", "frames_count": 3}
    
    response = client.post(
        "/incidents/inc_123/analyze",
        json={"workspace_id": "ws_123"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "analyzed"
    assert response.json()["frames_count"] == 3
