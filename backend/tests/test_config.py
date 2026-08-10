import pytest
from pydantic import ValidationError
from app.core.config import Settings

def test_config_loads_successfully(monkeypatch) -> None:
    """
    Verifies that the configuration loads properly when all required variables are set.
    """
    # Clean environment variables first
    monkeypatch.setenv("GITHUB_TOKEN", "mock_token")
    monkeypatch.setenv("GITHUB_APP_ID", "mock_app_id")
    monkeypatch.setenv("GITHUB_PRIVATE_KEY", "mock_private_key")
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("LLM_API_KEY", "mock_api_key")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/db")
    monkeypatch.setenv("SANDBOX_IMAGE", "mock_sandbox_image")

    # Instantiate Settings bypassing .env file loading to test environment loading directly
    settings = Settings(_env_file=None)
    
    assert settings.GITHUB_TOKEN == "mock_token"
    assert settings.GITHUB_APP_ID == "mock_app_id"
    assert settings.GITHUB_PRIVATE_KEY == "mock_private_key"
    assert settings.LLM_PROVIDER == "anthropic"
    assert settings.LLM_API_KEY == "mock_api_key"
    assert settings.DATABASE_URL == "postgresql://user:pass@localhost:5432/db"
    assert settings.SANDBOX_IMAGE == "mock_sandbox_image"

def test_config_missing_required_field_raises_error(monkeypatch) -> None:
    """
    Verifies that missing required configuration fields raise validation errors.
    """
    monkeypatch.setenv("GITHUB_TOKEN", "mock_token")
    monkeypatch.setenv("GITHUB_APP_ID", "mock_app_id")
    monkeypatch.setenv("GITHUB_PRIVATE_KEY", "mock_private_key")
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_API_KEY", "mock_api_key")
    # DATABASE_URL is missing
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("SANDBOX_IMAGE", "mock_sandbox_image")

    with pytest.raises(ValidationError) as exc_info:
        Settings(_env_file=None)
    
    # Assert DATABASE_URL is the cause of validation failure
    assert "DATABASE_URL" in str(exc_info.value)
