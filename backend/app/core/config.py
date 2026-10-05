"""Typed application configuration loaded from the repository root."""

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal, Self

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


def repository_env_file(config_file: Path = Path(__file__)) -> Path:
    """Resolve the repository-root env file independently of the working directory."""
    return config_file.resolve().parents[3] / ".env"


ENV_FILE = repository_env_file()


class Settings(BaseSettings):
    """Backend environment settings."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: Literal["development", "staging", "production"]
    demo_mode: bool
    api_base_path: str = "/api/v1"
    cors_origins: Annotated[tuple[str, ...], NoDecode]
    database_url: str
    test_database_url: str | None = None
    redis_url: str
    test_redis_url: str | None = None
    run_migrations: bool = False
    jwt_secret: SecretStr
    jwt_expires_minutes: int = Field(default=720, gt=0)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    timezone_display: str = "Asia/Karachi"
    upload_max_mb: int = Field(default=10, gt=0)
    upload_max_rows: int = Field(default=5000, gt=0)
    preview_ttl_minutes: int = Field(default=30, gt=0)
    media_storage_dir: Path
    media_public_url: str
    messaging_provider: Literal["simulator"]
    dispatcher_interval_seconds: float = Field(default=5, gt=0)
    dispatcher_batch_size: int = Field(default=100, gt=0, le=1000)
    sim_delivery_delay_seconds: float = Field(default=2, ge=0)
    sim_auto_read_rate: float = Field(default=0.6, ge=0, le=1)
    sim_auto_read_delay_seconds: float = Field(default=10, ge=0)
    sim_typing_seconds: float = Field(default=1.5, ge=0)
    llm_enabled: bool | None = None
    llm_provider_order: Annotated[tuple[str, ...], NoDecode] | None = None
    llm_timeout_seconds: float | None = Field(default=None, gt=0)
    llm_max_retries_per_provider: int | None = Field(default=None, ge=0)
    llm_total_budget_seconds: float | None = Field(default=None, gt=0)
    llm_circuit_failures: int | None = Field(default=None, gt=0)
    llm_circuit_cooldown_seconds: float | None = Field(default=None, gt=0)
    groq_api_key: SecretStr | None = None
    groq_model: str | None = None
    cerebras_api_key: SecretStr | None = None
    cerebras_model: str | None = None
    gemini_api_key: SecretStr | None = None
    gemini_model: str | None = None
    mistral_api_key: SecretStr | None = None
    mistral_model: str | None = None
    together_api_key: SecretStr | None = None
    together_model: str | None = None
    openrouter_api_key: SecretStr | None = None
    openrouter_model: str | None = None
    agent_confidence_threshold: float | None = Field(default=None, ge=0, le=1)
    langsmith_tracing: bool | None = None
    langsmith_api_key: SecretStr | None = None
    langsmith_project: str | None = None
    langsmith_endpoint: str | None = None
    seed_admin_email: str | None = None
    seed_admin_password: SecretStr | None = None
    seed_coordinator_email: str | None = None
    seed_coordinator_password: SecretStr | None = None

    @field_validator("cors_origins", "llm_provider_order", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        """Parse documented comma-separated setting lists."""
        if not isinstance(value, str):
            return value
        return tuple(origin.strip() for origin in value.split(",") if origin.strip())

    @model_validator(mode="after")
    def validate_optional_integrations(self) -> Self:
        """Require provider credentials only when their integration is enabled."""
        if self.langsmith_tracing and not self.langsmith_api_key:
            raise ValueError("LANGSMITH_API_KEY is required when LangSmith tracing is enabled")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings()
