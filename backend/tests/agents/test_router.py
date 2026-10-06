"""Provider fallback, terminal auth, budget, and circuit behavior."""

import asyncio

import pytest
from pydantic import BaseModel

from app.agents.llm.providers import EnabledProvider
from app.agents.llm.router import LLMRouter, RoutingUnavailable, routing_context
from tests.agents.fakes import CircuitStore, router_settings


class ProbeResult(BaseModel):
    """Minimal structured output for router tests."""

    value: str


class ProviderHttpError(RuntimeError):
    """Provider-like error carrying an HTTP status."""

    def __init__(self, status_code: int) -> None:
        super().__init__(f"status {status_code}")
        self.status_code = status_code


@pytest.mark.asyncio
async def test_router_falls_back_in_configured_order() -> None:
    calls: list[str] = []

    async def invoke(provider: EnabledProvider, schema: type[BaseModel], prompt: str) -> BaseModel:
        del prompt
        calls.append(provider.definition.name)
        if provider.definition.name == "groq":
            raise TimeoutError
        return schema.model_validate({"value": "ok"})

    router = LLMRouter(router_settings(), CircuitStore(), provider_invoker=invoke)
    async with routing_context(router) as stats:
        result = await router.get_structured_llm(ProbeResult).ainvoke("safe input")

    assert result.value == "ok"
    assert calls == ["groq", "cerebras"]
    assert stats.provider == "cerebras"
    assert stats.fallback_count == 1


@pytest.mark.asyncio
async def test_invalid_structured_output_uses_next_provider() -> None:
    calls: list[str] = []

    async def invoke(provider: EnabledProvider, schema: type[BaseModel], prompt: str) -> BaseModel:
        del prompt
        calls.append(provider.definition.name)
        if provider.definition.name == "groq":
            return schema.model_validate({"not_value": "invalid"})
        return schema.model_validate({"value": "valid"})

    router = LLMRouter(router_settings(), CircuitStore(), provider_invoker=invoke)
    result = await router.invoke(ProbeResult, "safe input")

    assert result == ProbeResult(value="valid")
    assert calls == ["groq", "cerebras"]


@pytest.mark.asyncio
async def test_auth_failure_stops_fallback_and_marks_provider_unavailable() -> None:
    calls: list[str] = []

    async def invoke(provider: EnabledProvider, schema: type[BaseModel], prompt: str) -> BaseModel:
        del prompt
        calls.append(provider.definition.name)
        if provider.definition.name == "groq":
            raise ProviderHttpError(401)
        return schema.model_validate({"value": "second call"})

    router = LLMRouter(router_settings(), CircuitStore(), provider_invoker=invoke)
    with pytest.raises(RoutingUnavailable):
        await router.invoke(ProbeResult, "safe input")
    assert calls == ["groq"]

    result = await router.invoke(ProbeResult, "safe input")
    assert result == ProbeResult(value="second call")
    assert calls == ["groq", "cerebras"]


@pytest.mark.asyncio
async def test_circuit_opens_after_consecutive_failures() -> None:
    calls: list[str] = []

    async def invoke(provider: EnabledProvider, schema: type[BaseModel], prompt: str) -> BaseModel:
        del prompt
        calls.append(provider.definition.name)
        if provider.definition.name == "groq":
            raise ProviderHttpError(503)
        return schema.model_validate({"value": "ok"})

    router = LLMRouter(router_settings(), CircuitStore(), provider_invoker=invoke)
    await router.invoke(ProbeResult, "one")
    await router.invoke(ProbeResult, "two")
    await router.invoke(ProbeResult, "three")

    assert calls == ["groq", "cerebras", "groq", "cerebras", "cerebras"]


@pytest.mark.asyncio
async def test_total_budget_bounds_a_slow_provider() -> None:
    async def invoke(provider: EnabledProvider, schema: type[BaseModel], prompt: str) -> BaseModel:
        del provider, prompt
        await asyncio.sleep(1)
        return schema.model_validate({"value": "late"})

    settings = router_settings(
        llm_provider_order=("groq",),
        llm_timeout_seconds=1.0,
        llm_total_budget_seconds=0.02,
    )
    router = LLMRouter(settings, CircuitStore(), provider_invoker=invoke)

    with pytest.raises(RoutingUnavailable):
        await router.invoke(ProbeResult, "safe input")


@pytest.mark.asyncio
async def test_startup_missing_model_skips_provider_without_crashing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = False

    async def invoke(provider: EnabledProvider, schema: type[BaseModel], prompt: str) -> BaseModel:
        nonlocal called
        del provider, prompt
        called = True
        return schema.model_validate({"value": "unexpected"})

    async def unavailable(*args: object) -> bool:
        del args
        return False

    settings = router_settings(llm_provider_order=("groq",))
    router = LLMRouter(settings, CircuitStore(), provider_invoker=invoke)
    monkeypatch.setattr("app.agents.llm.router.model_available", unavailable)

    await router.check_models()

    with pytest.raises(RoutingUnavailable):
        await router.invoke(ProbeResult, "safe input")
    assert called is False
