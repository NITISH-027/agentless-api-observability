import httpx
import logging
from typing import Dict, Any, List, Optional
import asyncio
import os
logger = logging.getLogger("app.services.analysis.llm_provider")

class BaseLLMProvider:
    """
    Abstract interface for LLM model providers.
    """
    async def complete(self, prompt: str, system_instruction: str) -> str:
        raise NotImplementedError("Subclasses must implement complete()")

class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI chat completion provider using standard HTTP requests.
    """
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", timeout_seconds: float = 30.0):
        self.api_key = api_key
        self.model = model
        self.timeout = timeout_seconds

    async def complete(self, prompt: str, system_instruction: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"}
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    logger.error(f"OpenAI API call failed with status {resp.status_code}: {resp.text}")
                    raise ValueError(f"OpenAI API Error ({resp.status_code}): {resp.text}")
            except httpx.TimeoutException as e:
                logger.error(f"OpenAI API request timed out: {e}")
                raise asyncio.TimeoutError("OpenAI API request timed out")
            except httpx.RequestError as e:
                logger.error(f"OpenAI request network failure: {e}")
                raise ValueError(f"OpenAI network error: {e}")

class MockLLMProvider(BaseLLMProvider):
    """
    Mock LLM provider used to simulate model completions during unit tests.
    """
    def __init__(self, response_text: str = "", simulate_timeout: bool = False, simulate_failure: bool = False):
        self.response_text = response_text
        self.simulate_timeout = simulate_timeout
        self.simulate_failure = simulate_failure

    async def complete(self, prompt: str, system_instruction: str) -> str:
        # Prioritize patch detection before hypotheses to ensure correct response for patch generation.
        if self.simulate_timeout:
            await asyncio.sleep(0.5)
            raise asyncio.TimeoutError("Simulated API timeout")
        if self.simulate_failure:
            raise ValueError("Simulated API connection failure")
        if self.response_text:
            return self.response_text

        import json
        prompt_lower = (prompt + " " + system_instruction).lower()
        # Detect patch generation request first.
        if "patch" in prompt_lower or "diff" in prompt_lower:
            diff = (
                "diff --git a/app/orders.py b/app/orders.py\n"
                "--- a/app/orders.py\n"
                "+++ b/app/orders.py\n"
                "@@ -1,5 +1,6 @@\n"
                "def calculate_total(price: float, quantity: int):\n"
                "-    if quantity < 0:\n"
                "-        raise ValueError(\"quantity cannot be negative\")\n"
                "+    if quantity < 0:\n"
                "+        from fastapi import HTTPException\n"
                "+        raise HTTPException(status_code=400, detail=\"quantity cannot be negative\")\n"
                "\n"
                "    return price * quantity\n"
            )
            return json.dumps({
                "files_to_modify": ["app/orders.py"],
                "patch_diff": diff,
                "explanation": "Replace unhandled ValueError with HTTPException(400).",
                "root_cause_addressed": "Unhandled ValueError exception on negative input",
                "tests_added_or_modified": [],
                "risk_notes": "None"
            })
        # Then handle hypothesis generation.
        if "hypotheses" in prompt_lower or "hypothesis" in prompt_lower:
            return json.dumps({
                "hypotheses": [
                    {
                        "id": "hyp_1",
                        "title": "Missing Input Quantity Validation",
                        "category": "CODE",
                        "description": "Negative quantity values are not properly validated or converted to HTTP 400 responses, causing uncaught ValueError exceptions.",
                        "affected_files": ["app/orders.py"],
                        "affected_lines": [3],
                        "supporting_evidence": ["ValueError: quantity cannot be negative at app/orders.py line 3"],
                        "contradicting_evidence": [],
                        "confidence": "HIGH",
                        "verification_plan": ["Send negative quantity payload and assert response status code 400"]
                    }
                ]
            })
        # Reproducer code generation.
        if "reproducer" in prompt_lower or "pytest" in prompt_lower:
            test_code = (
                "from fastapi.testclient import TestClient\n"
                "from app.main import app\n\n"
                "client = TestClient(app)\n\n"
                "def test_negative_quantity_should_be_rejected():\n"
                "    response = client.post('/orders', json={'product_id': 101, 'quantity': -2})\n"
                "    assert response.status_code == 400\n"
            )
            return json.dumps({"test_code": test_code})
        return "{}"

def get_llm_provider(provider_name: str, api_key: str) -> BaseLLMProvider:
    """
    Factory to retrieve configured LLM Provider.
    """
    name = provider_name.lower().strip()
    if name == "openai":
        # Ensure a key is present; also verify the environment variable is set for safety.
        if not api_key or os.getenv("LLM_API_KEY") is None:
            raise ValueError("OpenAI provider selected but LLM_API_KEY is missing")
        return OpenAIProvider(api_key=api_key)
    elif name == "mock":
        return MockLLMProvider()
    else:
        raise ValueError(f"Unsupported LLM provider: {provider_name}")
