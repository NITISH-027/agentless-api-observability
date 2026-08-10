import json
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from app.models.incident import Incident
from app.services.analysis.llm_provider import BaseLLMProvider

logger = logging.getLogger("app.services.reproduction.reproducer_generator")

class TestCodeModel(BaseModel):
    test_code: str = Field(..., description="Complete python pytest test code to reproduce the failure")

def build_reproducer_prompt(incident: Incident, traceback_analysis: Dict[str, Any]) -> str:
    prompt = f"""You are generating a minimal Pytest reproducer test script for an API failure.
The goal of the test script is to call the target repository function/class to reproduce the EXACT exception observed.

[INCIDENT DETAILS]
Exception: {incident.error_type} - {incident.error_message}
Request Method: {incident.request_method}
Request Path: {incident.request_path}
Request Body: {json.dumps(incident.request_body or {})}
Request Query: {json.dumps(incident.request_query or {})}

[STACK TRACE]
{incident.error_stack_trace}
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
1. Write a standard pytest function, for example: `def test_reproduce_exception():`
2. It should import the necessary modules from the workspace repository (e.g., `from src.service import ...`).
3. Invoke the code with the exact parameters/payload to cause the original exception to be raised.
4. Do NOT catch the exception inside the test. Let the exception bubble up to pytest so pytest records a test FAILURE.
5. Avoid using production secrets.
6. The output must be valid, executable Python code.
"""
    return prompt

class ReproducerGenerator:
    async def generate_reproducer(
        self,
        incident: Incident,
        traceback_analysis: Dict[str, Any],
        provider: BaseLLMProvider,
        max_retries: int = 3
    ) -> str:
        prompt = build_reproducer_prompt(incident, traceback_analysis)
        
        system_instruction = (
            "You are a test code generation agent. Output exactly a JSON object matching this schema:\n"
            '{"test_code": "def test_reproduce_exception():\\n    # import and call"}\n'
            "Return only valid JSON. Do not include markdown code block formatting."
        )
        
        retries = 0
        validation_error = ""
        while retries < max_retries:
            try:
                current_sys = system_instruction
                if validation_error:
                    current_sys += f"\nYour previous output failed validation: {validation_error}. Please output valid JSON."
                    
                raw_response = await provider.complete(prompt, current_sys)
                
                # Clean markdown format if returned
                json_str = raw_response.strip()
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0].strip()
                    
                data = json.loads(json_str)
                validated = TestCodeModel.model_validate(data)
                
                logger.info("Successfully generated Pytest reproducer code.")
                return validated.test_code
                
            except Exception as e:
                retries += 1
                validation_error = str(e)
                logger.warning(f"Reproducer generation attempt {retries} failed: {e}")
                
        raise ValueError(f"Failed to generate reproducer after {max_retries} attempts: {validation_error}")
