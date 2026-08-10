import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, ValidationError

# Resolve directory paths dynamically to find the correct .env file
CURRENT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = CURRENT_DIR.parent.parent
ROOT_DIR = BACKEND_DIR.parent

env_paths = [
    ROOT_DIR / ".env",
    BACKEND_DIR / ".env",
    Path(".env")
]

selected_env_file = Path(".env")
for path in env_paths:
    if path.exists():
        selected_env_file = path
        break

class Settings(BaseSettings):
    GITHUB_TOKEN: str = Field(..., description="GitHub API Personal Access Token")
    GITHUB_APP_ID: str = Field(..., description="GitHub App ID")
    GITHUB_PRIVATE_KEY: str = Field(..., description="GitHub App Private Key (RSA Private Key)")
    LLM_PROVIDER: str = Field("openai", description="LLM provider: openai, anthropic, gemini, etc.")
    LLM_API_KEY: str = Field(..., description="LLM provider API key")
    DATABASE_URL: str = Field(..., description="Supabase PostgreSQL connection URL")
    SANDBOX_IMAGE: str = Field("python:3.10-slim", description="Docker image for isolated reproduction")

    model_config = SettingsConfigDict(
        env_file=str(selected_env_file),
        env_file_encoding="utf-8",
        extra="ignore"
    )

def get_settings() -> Settings:
    """Return a fresh Settings instance reflecting current environment variables.
    Previously this function cached a singleton instance, which prevented tests that
    monkey‑patch environment variables from seeing updated values. The new implementation
    always creates a new Settings object, ensuring that changes to LLM_PROVIDER or
    LLM_API_KEY are respected during each call.
    """
    return Settings()
