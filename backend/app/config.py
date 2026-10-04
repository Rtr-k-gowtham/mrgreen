"""
MR.GREEN — Application Configuration

All settings are loaded from environment variables via Pydantic BaseSettings.
Never hard-code secrets. Use .env for local development.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for the MR.GREEN application."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "MR.GREEN"
    app_env: str = "development"
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # Database
    database_url: str = "postgresql+asyncpg://mrgreen:mrgreen_dev_password@localhost:5432/mrgreen_db"

    # Ollama
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "qwen2.5:3b"
    ollama_embedding_model: str = "qwen2.5:3b"
    ollama_timeout: int = 120

    # Security
    secret_key: str = "change-me-to-a-random-secret-key"

    # Agent & Tool limits
    max_agent_iterations: int = 10
    agent_timeout_seconds: int = 300
    tool_timeout_seconds: int = 60
    workspace_dir: str = "workspace"
    max_tool_output_size: int = 500_000

    # Memory
    memory_extraction_enabled: bool = True
    short_term_memory_limit: int = 50

    # Logging
    log_level: str = "INFO"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
