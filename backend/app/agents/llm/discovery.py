"""Non-fatal startup validation of configured provider model IDs."""

from collections.abc import Mapping

import httpx
import structlog
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.agents.llm.providers import EnabledProvider

logger = structlog.get_logger(__name__)


class ModelEntry(BaseModel):
    """One provider model-list item."""

    model_config = ConfigDict(extra="ignore")
    id: str | None = None
    name: str | None = None


class ModelCatalog(BaseModel):
    """OpenAI-compatible or Gemini model-list response."""

    model_config = ConfigDict(extra="ignore")
    data: list[ModelEntry] = Field(default_factory=list)
    models: list[ModelEntry] = Field(default_factory=list)


async def model_available(client: httpx.AsyncClient, provider: EnabledProvider) -> bool:
    """Return false and warn when discovery fails or the configured model is absent."""
    name = provider.definition.name
    try:
        response = await client.get(
            f"{provider.definition.base_url}/models",
            headers=_headers(provider),
        )
        response.raise_for_status()
        models = _model_ids(ModelCatalog.model_validate(response.json()))
    except (httpx.HTTPError, ValidationError, ValueError) as error:
        logger.warning("llm_model_check_failed", provider=name, error_type=type(error).__name__)
        return False
    if provider.model not in models:
        logger.warning(
            "llm_configured_model_missing",
            provider=name,
            configured_model=provider.model,
            available_models=sorted(models),
        )
        return False
    return True


def _headers(provider: EnabledProvider) -> Mapping[str, str]:
    if provider.definition.client_type == "gemini":
        return {"x-goog-api-key": provider.api_key.get_secret_value()}
    return {"Authorization": f"Bearer {provider.api_key.get_secret_value()}"}


def _model_ids(catalog: ModelCatalog) -> set[str]:
    return {
        value.removeprefix("models/")
        for item in (*catalog.data, *catalog.models)
        if (value := item.id or item.name)
    }
