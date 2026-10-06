"""Provider registry configuration, discovery, and model overrides."""

import httpx
import pytest
from pydantic import SecretStr

from app.agents.llm.discovery import model_available
from app.agents.llm.providers import PROVIDERS, EnabledProvider, enabled_providers
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


@pytest.mark.asyncio
async def test_gemini_discovery_sends_key_only_in_header() -> None:
    secret = "gemini-configured-secret"
    provider = EnabledProvider(
        PROVIDERS["gemini"], SecretStr(secret), PROVIDERS["gemini"].default_model
    )

    async def respond(request: httpx.Request) -> httpx.Response:
        assert secret not in str(request.url)
        assert request.headers["x-goog-api-key"] == secret
        return httpx.Response(
            200,
            json={"models": [{"name": f"models/{provider.model}"}]},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
        assert await model_available(client, provider) is True
