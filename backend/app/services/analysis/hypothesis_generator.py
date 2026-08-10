import json
import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ValidationError
from typing import Literal
from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.services.github.workspace import WorkspaceManager
from app.services.analysis.llm_provider import BaseLLMProvider
from app.services.analysis.mapper import TracebackMapper

logger = logging.getLogger("app.services.analysis.hypothesis_generator")

# ==========================================
# Pydantic Schemas for Output Validation
# ==========================================
class HypothesisModel(BaseModel):
    id: str = Field(..., description="Unique slug identifier (e.g. hyp_1)")
    title: str = Field(..., description="DESCRIPTIVE title of the root cause")
    category: Literal["CODE", "CONFIG", "DATA", "DEPENDENCY", "UNKNOWN"]
    description: str = Field(..., description="Detailed explanation of the hypothesis claim")
    affected_files: List[str] = Field(default_factory=list, description="Source files in the repository implicated by this hypothesis")
    affected_lines: List[int] = Field(default_factory=list, description="Specific line numbers within those files")
    supporting_evidence: List[str] = Field(default_factory=list, description="Observations from logs/context supporting the claim")
    contradicting_evidence: List[str] = Field(default_factory=list, description="Concrete observations arguing against the claim, or blank if none")
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    verification_plan: List[str] = Field(..., description="Experimental steps to test/validate this hypothesis")

class HypothesisList(BaseModel):
    hypotheses: List[HypothesisModel]

# ==========================================
# Prompt Construction
# ==========================================
def build_investigation_prompt(incident: Incident, analysis: Dict[str, Any]) -> str:
    # 1. Base incident information
    prompt = f"""You are analyzing a service exception to generate at most 3 competing debugging hypotheses.

[INCIDENT DETAILS]
Service: {incident.service}
Environment: {incident.environment}
Timestamp: {incident.timestamp}
Exception: {incident.error_type} - {incident.error_message}

[HTTP REQUEST]
Method: {incident.request_method}
Path: {incident.request_path}
Query Parameters: {json.dumps(incident.request_query or {})}
Headers: {json.dumps(incident.request_headers or {})}
Body: {json.dumps(incident.request_body or {})}

[HTTP RESPONSE]
Status Code: {incident.response_status_code}
Body: {json.dumps(incident.response_body or {})}

[STACK TRACE]
{incident.error_stack_trace}
"""

    # 2. Source Code Context (Frames mapped from traceback)
    prompt += "\n[RELEVANT SOURCE CODE CONTEXT]\n"
    for frame in analysis.get("frames", []):
        if not frame.get("mapped"):
            prompt += f"External Frame: File {frame.get('raw_file_path')}, line {frame.get('line_number')}, in {frame.get('function_name')}\n"
            continue
            
        prompt += f"Mapped File: {frame.get('repo_path')}\n"
        prompt += f"Scope: Class '{frame.get('containing_class')}', Function '{frame.get('containing_function')}'\n"
        prompt += f"Target Line: {frame.get('line_number')}\n"
        prompt += "Code Lines:\n"
        for line in frame.get("context", []):
            marker = "--> " if line.get("is_target") else "    "
            prompt += f"{marker}{line.get('line_number')}: {line.get('content')}\n"
        prompt += "---------------------------------------\n"

    # 3. Call Relationships
    prompt += "\n[CALL GRAPH RELATIONSHIPS]\n"
    for relation in analysis.get("call_graph", []):
        parent_info = f"{relation['parent']['file']}:{relation['parent']['function']}"
        child_info = f"{relation['child']['file']}:{relation['child']['function']}"
        prompt += f"- {parent_info} -> {child_info} (Relationship status: {relation['relationship']})\n"

    # 4. Strict instructions
    prompt += """
[CRITICAL INSTRUCTIONS]
1. Generate at most 3 competing debugging hypotheses that explain why this error happened.
2. Ground every claim strictly in the provided evidence.
3. Every file path in 'affected_files' MUST exist in the provided repository mapped files list.
4. Do NOT hallucinate files, lines, calls, or variable values.
5. If there is not enough evidence to confirm a claim, list it under 'contradicting_evidence' or explain it in the description, or output 'Insufficient evidence'.
6. Do NOT suggest code patches or fixes yet. Focus purely on diagnosing the root cause.
"""
    return prompt

# ==========================================
# Hypothesis Generator Class
# ==========================================
class HypothesisGenerator:
    """
    Manages prompting an LLM Provider, validating structured output, checking
    for hallucinated file references, and updating incident evidence.
    """
    def __init__(self, workspace_manager: Optional[WorkspaceManager] = None):
        self.wm = workspace_manager or WorkspaceManager()

    async def generate_hypotheses(
        self,
        db: Session,
        incident_id: str,
        workspace_id: str,
        provider: BaseLLMProvider,
        max_retries: int = 3
    ) -> List[Dict[str, Any]]:
        # 1. Retrieve Incident
        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            raise ValueError(f"Incident {incident_id} not found")

        # 2. Check if traceback mapping is completed, run if missing
        analysis = incident.traceback_analysis
        if not analysis:
            logger.info(f"Traceback analysis missing for {incident_id}. Running mapper...")
            mapper = TracebackMapper(self.wm)
            analysis = mapper.analyze_incident_traceback(db, incident_id, workspace_id)

        # 3. Retrieve files in workspace repository to validate hallucinations
        try:
            repo_files = self.wm.list_files(workspace_id)
        except Exception as e:
            raise ValueError(f"Workspace {workspace_id} repository is inaccessible: {e}")

        # 4. Build prompt
        prompt = build_investigation_prompt(incident, analysis)
        
        # 5. Formulate structured schema validation instructions
        system_instruction = (
            "You are a principal debugging assistant. Your task is to output a JSON object containing "
            "competing debugging hypotheses explaining the incident. Your output must strictly match the following JSON schema:\n"
            "{\n"
            '  "hypotheses": [\n'
            "    {\n"
            '      "id": "hyp_1",\n'
            '      "title": "Short Descriptive Title",\n'
            '      "category": "CODE",\n'  # must be CODE, CONFIG, DATA, DEPENDENCY, or UNKNOWN
            '      "description": "Detailed claim analysis.",\n'
            '      "affected_files": ["src/orders/service.py"],\n' # MUST exist in the provided list
            '      "affected_lines": [87],\n'
            '      "supporting_evidence": ["observation 1"],\n'
            '      "contradicting_evidence": ["observation 2"],\n'
            '      "confidence": "HIGH",\n'  # must be HIGH, MEDIUM, or LOW
            '      "verification_plan": ["test step 1"]\n'
            "    }\n"
            "  ]\n"
            "}\n"
            "Return only valid JSON. Do not include markdown code block formatting (like ```json) if possible, or wrap it cleanly. "
            "Never invent file paths or code files."
        )

        # 6. Retry Loop for LLM calls & schema validation
        retries = 0
        validation_error_log = ""
        
        while retries < max_retries:
            try:
                # Add validation details to help model auto-correct on retries
                current_sys_instruction = system_instruction
                if validation_error_log:
                    current_sys_instruction += f"\n\n[RETRIAL ALERT] Your previous output failed validation: {validation_error_log}. Please correct the output."
                
                raw_response = await provider.complete(prompt, current_sys_instruction)
                
                # Sanitize response to pull JSON string
                json_str = raw_response.strip()
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0].strip()
                
                data = json.loads(json_str)
                
                # Pydantic schema check
                validated_payload = HypothesisList.model_validate(data)
                hypotheses = validated_payload.hypotheses
                
                # Check for hallucinated files
                for hyp in hypotheses:
                    hallucinated = [f for f in hyp.affected_files if f not in repo_files]
                    if hallucinated:
                        raise ValueError(
                            f"Hallucinated file paths detected: {hallucinated}. "
                            f"Implicated files must be present in the repository files list."
                        )
                
                # Check hypotheses limit (max 3)
                if len(hypotheses) > 3:
                    hypotheses = hypotheses[:3]
                
                # Save generated hypotheses list to database incident
                hypotheses_dict = [h.model_dump() for h in hypotheses]
                incident.hypotheses = hypotheses_dict
                db.commit()
                
                logger.info(f"Successfully generated {len(hypotheses_dict)} hypotheses for incident {incident_id}")
                return hypotheses_dict

            except Exception as e:
                retries += 1
                validation_error_log = str(e)
                logger.warning(f"Hypothesis generation attempt {retries} failed: {e}")
                
        # Raise failure if retries run out
        raise ValueError(
            f"Failed to generate structured hypotheses after {max_retries} attempts. "
            f"Last validation error: {validation_error_log}"
        )
