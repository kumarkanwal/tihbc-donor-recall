"""In-memory LLM router collaborators for agent tests."""

from collections.abc import Awaitable, Callable

from pydantic import BaseModel, SecretStr

from app.agents.llm.providers import EnabledProvider
from app.core.config import Settings


class CircuitStore:
    """Small Redis-compatible circuit store."""

    def __init__(self) -> None:
        self.values: dict[str, int | str] = {}

    async def exists(self, key: str) -> int:
        return int(key in self.values)

    async def incr(self, key: str) -> int:
        value = int(self.values.get(key, 0)) + 1
        self.values[key] = value
        return value

    async def expire(self, key: str, seconds: int) -> bool:
        del seconds
        return key in self.values

    async def set(self, key: str, value: str, *, ex: int) -> object:
        del ex
        self.values[key] = value
        return True

    async def delete(self, *keys: str) -> int:
        deleted = 0
        for key in keys:
            deleted += int(self.values.pop(key, None) is not None)
        return deleted


ProviderInvoker = Callable[[EnabledProvider, type[BaseModel], str], Awaitable[BaseModel]]


def router_settings(**updates: object) -> Settings:
    """Build valid settings with two fake enabled providers."""
    defaults: dict[str, object] = {
        "llm_provider_order": ("groq", "cerebras"),
        "groq_api_key": SecretStr("groq-secret"),
        "cerebras_api_key": SecretStr("cerebras-secret"),
        "llm_timeout_seconds": 0.5,
        "llm_total_budget_seconds": 1.5,
        "llm_circuit_failures": 2,
        "llm_circuit_cooldown_seconds": 30,
    }
    defaults.update(updates)
    return Settings().model_copy(update=defaults)
