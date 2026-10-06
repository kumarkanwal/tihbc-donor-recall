"""Provider registry configuration and model overrides."""

from pydantic import SecretStr

from app.agents.llm.providers import PROVIDERS, enabled_providers
from tests.agents.fakes import router_settings


def test_registry_contains_every_documented_provider() -> None:
    assert tuple(PROVIDERS) == (
        "groq",
        "cerebras",
        "gemini",
        "mistral",
        "together",
        "openrouter",
    )
    assert all(provider.default_model for provider in PROVIDERS.values())


def test_only_keys_enable_providers_and_model_override_wins() -> None:
    settings = router_settings(
        llm_provider_order=("groq", "gemini", "openrouter"),
        groq_model="custom-structured-model",
        gemini_api_key=SecretStr("gemini-secret"),
        openrouter_api_key=None,
    )

    providers = enabled_providers(settings)

    assert [provider.definition.name for provider in providers] == ["groq", "gemini"]
    assert providers[0].model == "custom-structured-model"
