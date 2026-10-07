"""Provider registry and LangChain client construction."""

from dataclasses import dataclass
from typing import Literal

from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mistralai import ChatMistralAI
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.core.config import Settings

ClientType = Literal["openai", "gemini", "mistral"]
GROQ_STRICT_JSON_SCHEMA_MODELS = frozenset(
    {"openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"}
)


@dataclass(frozen=True)
class ProviderDefinition:
    """Static configuration for one supported inference provider."""

    name: str
    base_url: str
    key_setting: str
    model_setting: str
    client_type: ClientType
    default_model: str


PROVIDERS = {
    "groq": ProviderDefinition(
        "groq",
        "https://api.groq.com/openai/v1",
        "groq_api_key",
        "groq_model",
        "openai",
        "openai/gpt-oss-20b",
    ),
    "cerebras": ProviderDefinition(
        "cerebras",
        "https://api.cerebras.ai/v1",
        "cerebras_api_key",
        "cerebras_model",
        "openai",
        "gpt-oss-120b",
    ),
    "gemini": ProviderDefinition(
        "gemini",
        "https://generativelanguage.googleapis.com/v1beta",
        "gemini_api_key",
        "gemini_model",
        "gemini",
        "gemini-2.5-flash-lite",
    ),
    "mistral": ProviderDefinition(
        "mistral",
        "https://api.mistral.ai/v1",
        "mistral_api_key",
        "mistral_model",
        "mistral",
        "ministral-8b-latest",
    ),
    "together": ProviderDefinition(
        "together",
        "https://api.together.xyz/v1",
        "together_api_key",
        "together_model",
        "openai",
        "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free",
    ),
    "openrouter": ProviderDefinition(
        "openrouter",
        "https://openrouter.ai/api/v1",
        "openrouter_api_key",
        "openrouter_model",
        "openai",
        "openrouter/free",
    ),
}


@dataclass(frozen=True)
class EnabledProvider:
    """A provider resolved from settings without exposing its key in logs."""

    definition: ProviderDefinition
    api_key: SecretStr
    model: str


def enabled_providers(settings: Settings) -> tuple[EnabledProvider, ...]:
    """Resolve configured providers in the documented order."""
    enabled: list[EnabledProvider] = []
    for name in settings.llm_provider_order:
        definition = PROVIDERS.get(name)
        if definition is None:
            continue
        key = getattr(settings, definition.key_setting)
        if not isinstance(key, SecretStr) or not key.get_secret_value().strip():
            continue
        override = getattr(settings, definition.model_setting)
        model = override.strip() if isinstance(override, str) and override.strip() else None
        enabled.append(EnabledProvider(definition, key, model or definition.default_model))
    return tuple(enabled)


def create_chat_model(provider: EnabledProvider, settings: Settings) -> BaseChatModel:
    """Build the provider-specific LangChain chat client at temperature zero."""
    definition = provider.definition
    common = {"temperature": 0, "model": provider.model}
    if definition.client_type == "gemini":
        return ChatGoogleGenerativeAI(
            **common,
            api_key=provider.api_key,
            request_timeout=settings.llm_timeout_seconds,
            retries=settings.llm_max_retries_per_provider,
        )
    if definition.client_type == "mistral":
        return ChatMistralAI(
            model_name=provider.model,
            temperature=0,
            api_key=provider.api_key,
            base_url=definition.base_url,
            timeout=int(settings.llm_timeout_seconds),
            max_retries=settings.llm_max_retries_per_provider,
        )
    return ChatOpenAI(
        **common,
        api_key=provider.api_key,
        base_url=definition.base_url,
        timeout=settings.llm_timeout_seconds,
        max_retries=settings.llm_max_retries_per_provider,
    )


def structured_output_strict(provider: EnabledProvider) -> bool | None:
    """Use Groq constrained decoding when its configured model supports it."""
    if provider.definition.name == "groq" and provider.model in GROQ_STRICT_JSON_SCHEMA_MODELS:
        return True
    return None
