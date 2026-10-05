"""Tests for typed environment configuration."""

from pathlib import Path

import pytest

from app.core.config import ENV_FILE, Settings, repository_env_file

REQUIRED_ENVIRONMENT = (
    "APP_ENV=development",
    "DEMO_MODE=true",
    "CORS_ORIGINS=http://localhost:3000",
    "DATABASE_URL=postgresql+asyncpg://test:test@localhost:5432/test",
    "REDIS_URL=redis://localhost:6379/15",
    "JWT_SECRET=test-secret",
    "MEDIA_STORAGE_DIR=./test-media",
    "MEDIA_PUBLIC_URL=http://localhost:8000/media",
    "MESSAGING_PROVIDER=simulator",
)


def _clear_settings_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    for field_name in Settings.model_fields:
        monkeypatch.delenv(field_name.upper(), raising=False)


def _write_environment(path: Path, *overrides: str) -> None:
    overridden_names = {entry.partition("=")[0] for entry in overrides}
    values = [
        entry for entry in REQUIRED_ENVIRONMENT if entry.partition("=")[0] not in overridden_names
    ]
    path.write_text("\n".join((*values, *overrides)), encoding="utf-8")


def test_settings_load_root_env_from_backend_working_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = tmp_path / "repository"
    backend = repository / "backend"
    config_file = backend / "app" / "core" / "config.py"
    config_file.parent.mkdir(parents=True)
    config_file.touch()
    env_file = repository / ".env"
    _write_environment(
        env_file,
        "APP_ENV=staging",
        "DEMO_MODE=false",
        "CORS_ORIGINS=https://one.example.com, https://two.example.com",
        "DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/app",
        "REDIS_URL=redis://redis:6379/0",
        "RUN_MIGRATIONS=true",
        "JWT_SECRET=secret",
        "MEDIA_STORAGE_DIR=/data/media",
        "MEDIA_PUBLIC_URL=https://api.example.com/media",
        "LLM_ENABLED=false",
        "LANGSMITH_TRACING=false",
    )
    _clear_settings_environment(monkeypatch)
    monkeypatch.chdir(backend)

    resolved_env_file = repository_env_file(config_file)
    settings = Settings(_env_file=resolved_env_file)

    assert resolved_env_file.is_absolute()
    assert resolved_env_file == env_file
    assert settings.app_env == "staging"
    assert settings.demo_mode is False
    assert settings.cors_origins == (
        "https://one.example.com",
        "https://two.example.com",
    )
    assert settings.api_base_path == "/api/v1"
    assert settings.jwt_expires_minutes == 720
    assert settings.run_migrations is True
    assert settings.media_storage_dir == Path("/data/media")
    assert settings.dispatcher_batch_size == 100


def test_production_env_path_is_absolute() -> None:
    assert ENV_FILE.is_absolute()
    assert ENV_FILE.name == ".env"


def test_environment_variable_overrides_env_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / ".env"
    _write_environment(env_file, "APP_ENV=staging")
    _clear_settings_environment(monkeypatch)
    monkeypatch.setenv("APP_ENV", "production")

    settings = Settings(_env_file=env_file)

    assert settings.app_env == "production"


def test_later_integration_settings_are_optional(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / ".env"
    _write_environment(env_file)
    _clear_settings_environment(monkeypatch)

    settings = Settings(_env_file=env_file)

    assert settings.llm_provider_order is None
    assert settings.groq_api_key is None
    assert settings.openrouter_api_key is None
    assert settings.langsmith_api_key is None
    assert settings.seed_admin_email is None


def test_migrations_are_disabled_by_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    env_file = tmp_path / ".env"
    _write_environment(env_file)
    _clear_settings_environment(monkeypatch)

    settings = Settings(_env_file=env_file)

    assert settings.run_migrations is False
