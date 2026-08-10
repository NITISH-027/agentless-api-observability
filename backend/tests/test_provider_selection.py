import os
import pytest
from app.core.config import get_settings
from app.services.analysis.llm_provider import get_llm_provider, OpenAIProvider, MockLLMProvider


def test_openai_provider_selected_when_key_present(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    settings = get_settings()
    provider = get_llm_provider(settings.LLM_PROVIDER, settings.LLM_API_KEY)
    assert isinstance(provider, OpenAIProvider)
    assert provider.api_key == "test-key"


def test_mock_provider_selected_explicitly(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    settings = get_settings()
    provider = get_llm_provider("mock", settings.LLM_API_KEY)
    assert isinstance(provider, MockLLMProvider)


def test_missing_api_key_raises_error(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    if "LLM_API_KEY" in os.environ:
        monkeypatch.delenv("LLM_API_KEY", raising=False)
    settings = get_settings()
    with pytest.raises(ValueError, match="OpenAI provider selected but LLM_API_KEY is missing"):
        get_llm_provider(settings.LLM_PROVIDER, settings.LLM_API_KEY)
