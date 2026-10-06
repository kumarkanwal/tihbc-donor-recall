"""Redis-backed circuit state shared by LLM workers."""

from typing import Protocol, cast

from redis.asyncio import Redis


class CircuitStore(Protocol):
    """Redis operations required by the shared circuit breaker."""

    async def exists(self, key: str) -> int: ...

    async def incr(self, key: str) -> int: ...

    async def expire(self, key: str, seconds: int) -> bool: ...

    async def set(self, key: str, value: str, *, ex: int) -> object: ...

    async def delete(self, *keys: str) -> int: ...


class CircuitBreaker:
    """Count consecutive failures and cool down open provider circuits."""

    def __init__(
        self,
        redis: Redis | CircuitStore,
        *,
        failure_threshold: int,
        cooldown_seconds: float,
    ) -> None:
        self._redis = cast(CircuitStore, redis)
        self._failure_threshold = failure_threshold
        self._cooldown = max(1, int(cooldown_seconds))

    async def is_open(self, provider: str) -> bool:
        """Return whether a provider is in its shared cooldown window."""
        return bool(await self._redis.exists(_open_key(provider)))

    async def record_failure(self, provider: str) -> None:
        """Increment failure state and open the circuit at the threshold."""
        failure_key = _failure_key(provider)
        failures = await self._redis.incr(failure_key)
        await self._redis.expire(failure_key, self._cooldown)
        if failures < self._failure_threshold:
            return
        await self._redis.set(_open_key(provider), "1", ex=self._cooldown)
        await self._redis.delete(failure_key)

    async def reset(self, provider: str) -> None:
        """Clear shared failure and cooldown state after success."""
        await self._redis.delete(_failure_key(provider), _open_key(provider))


def _failure_key(provider: str) -> str:
    return f"llm:circuit:{provider}:failures"


def _open_key(provider: str) -> str:
    return f"llm:circuit:{provider}:open"
