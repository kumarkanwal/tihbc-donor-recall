"""Provider fallback, terminal auth, budget, and circuit behavior."""

import asyncio
from typing import Self

import pytest
import structlog
from google.genai.types import AutomaticFunctionCallingConfig
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel, SecretStr

from app.agents.llm.providers import EnabledProvider
from app.agents.llm.router import LLMRouter, RoutingUnavailable, routing_context
from tests.agents.fakes import CircuitStore, router_settings


class ProbeResult(BaseModel):
    """Minimal structured output for router tests."""

    value: str


class ProviderHttpError(RuntimeError):
    """Provider-like error carrying an HTTP status."""

    def __init__(self, status_code: int, body: object | None = None) -> None:
        super().__init__(f"status {status_code}")
        self.status_code = status_code
        self.body = body


class GeminiHttpError(RuntimeError):
    """Google GenAI-like error carrying its HTTP status as code."""

    def __init__(self, code: int) -> None:
        super().__init__(f"Gemini request failed with {code}")
        self.code = code


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
@pytest.mark.parametrize("status_code", [401, 403])
async def test_provider_credential_failure_continues_to_next_provider(
    status_code: int,
) -> None:
    calls: list[str] = []

    async def invoke(provider: EnabledProvider, schema: type[BaseModel], prompt: str) -> BaseModel:
        del prompt
        calls.append(provider.definition.name)
        if provider.definition.name == "groq":
            raise ProviderHttpError(status_code)
        return schema.model_validate({"value": "second call"})

    router = LLMRouter(router_settings(), CircuitStore(), provider_invoker=invoke)
    async with routing_context(router) as stats:
        result = await router.invoke(ProbeResult, "safe input")
    assert result == ProbeResult(value="second call")
    assert calls == ["groq", "cerebras"]
    assert [attempt.status for attempt in stats.attempts] == [
        "credentials_unavailable",
        "answered",
    ]


@pytest.mark.asyncio
async def test_rate_limit_then_payment_failure_reaches_gemini() -> None:
    calls: list[str] = []

    async def invoke(provider: EnabledProvider, schema: type[BaseModel], prompt: str) -> BaseModel:
        del prompt
        calls.append(provider.definition.name)
        if provider.definition.name == "groq":
            raise ProviderHttpError(429)
        if provider.definition.name == "cerebras":
            raise ProviderHttpError(402)
        return schema.model_validate({"value": "gemini answered"})

    settings = router_settings(
        llm_provider_order=("groq", "cerebras", "gemini"),
        gemini_api_key=SecretStr("gemini-secret"),
    )
    store = CircuitStore()
    router = LLMRouter(settings, store, provider_invoker=invoke)
    async with routing_context(router) as stats:
        result = await router.invoke(ProbeResult, "safe input")

    assert result == ProbeResult(value="gemini answered")
    assert calls == ["groq", "cerebras", "gemini"]
    assert [attempt.status for attempt in stats.attempts] == [
        "rate_limited",
        "payment_required",
        "answered",
    ]
    assert store.expirations["llm:circuit:cerebras:open"] == 300


@pytest.mark.asyncio
async def test_bad_request_logs_sanitized_body_and_uses_next_provider() -> None:
    secret = "groq-secret"

    async def invoke(provider: EnabledProvider, schema: type[BaseModel], prompt: str) -> BaseModel:
        del prompt
        if provider.definition.name == "groq":
            raise ProviderHttpError(
                400,
                {
                    "error": {
                        "message": f"invalid schema key={secret} for +923001234567",
                        "failed_generation": {"token": secret},
                    }
                },
            )
        return schema.model_validate({"value": "ok"})

    store = CircuitStore()
    with structlog.testing.capture_logs() as logs:
        result = await LLMRouter(router_settings(), store, provider_invoker=invoke).invoke(
            ProbeResult, "safe input"
        )

    rendered = repr(logs)
    assert result == ProbeResult(value="ok")
    assert secret not in rendered
    assert "+923001234567" not in rendered
    assert "+92300*****67" in rendered
    assert "failed_generation" in rendered
    assert store.expirations["llm:circuit:groq:open"] == 300


@pytest.mark.asyncio
async def test_output_parse_failure_uses_short_cooldown_and_fallback() -> None:
    calls: list[str] = []

    async def invoke(provider: EnabledProvider, schema: type[BaseModel], prompt: str) -> BaseModel:
        del prompt
        calls.append(provider.definition.name)
        if provider.definition.name == "groq":
            raise ProviderHttpError(
                400,
                {
                    "error": {
                        "code": "output_parse_failed",
                        "message": "Model emitted reasoning instead of JSON",
                    }
                },
            )
        return schema.model_validate({"value": "ok"})

    store = CircuitStore()
    router = LLMRouter(router_settings(), store, provider_invoker=invoke)
    with structlog.testing.capture_logs() as logs:
        async with routing_context(router) as stats:
            result = await router.invoke(ProbeResult, "asdfgh")

    assert result == ProbeResult(value="ok")
    assert calls == ["groq", "cerebras"]
    assert [attempt.status for attempt in stats.attempts] == ["invalid_output", "answered"]
    assert store.expirations["llm:circuit:groq:open"] == 30
    assert any(log["event"] == "llm_provider_fallback" for log in logs)
    assert all(log["event"] != "llm_provider_unavailable" for log in logs)


@pytest.mark.asyncio
async def test_groq_request_uses_strict_json_schema_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request_options: dict[str, object] = {}

    class FakeChatModel:
        def with_structured_output(
            self,
            schema: type[BaseModel],
            *,
            method: str,
            strict: bool | None,
        ) -> RunnableLambda[str, BaseModel]:
            request_options.update(method=method, strict=strict)

            async def answer(prompt: str) -> BaseModel:
                del prompt
                return schema.model_validate({"value": "ok"})

            return RunnableLambda(answer)

    monkeypatch.setattr(
        "app.agents.llm.router.create_chat_model",
        lambda provider, settings: FakeChatModel(),
    )
    router = LLMRouter(
        router_settings(llm_provider_order=("groq",)),
        CircuitStore(),
    )

    result = await router.invoke(ProbeResult, "safe input")

    assert result == ProbeResult(value="ok")
    assert request_options == {"method": "json_schema", "strict": True}


@pytest.mark.asyncio
async def test_gemini_uses_native_json_schema_with_afc_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request_options: dict[str, object] = {}

    class FakeStructuredModel:
        def __init__(self, schema: type[BaseModel]) -> None:
            self.schema = schema

        def bind(self, **kwargs: object) -> Self:
            request_options.update(kwargs)
            return self

        async def ainvoke(self, prompt: str) -> BaseModel:
            del prompt
            return self.schema.model_validate({"value": "ok"})

    class FakeChatModel:
        def with_structured_output(
            self,
            schema: type[BaseModel],
            *,
            method: str,
            strict: bool | None,
        ) -> FakeStructuredModel:
            request_options.update(method=method, strict=strict)
            return FakeStructuredModel(schema)

    monkeypatch.setattr(
        "app.agents.llm.router.create_chat_model",
        lambda provider, settings: FakeChatModel(),
    )
    settings = router_settings(
        llm_provider_order=("gemini",),
        gemini_api_key=SecretStr("gemini-secret"),
    )

    result = await LLMRouter(settings, CircuitStore()).invoke(ProbeResult, "safe input")

    afc = request_options["automatic_function_calling"]
    assert result == ProbeResult(value="ok")
    assert request_options["method"] == "json_schema"
    assert request_options["strict"] is None
    assert isinstance(afc, AutomaticFunctionCallingConfig)
    assert afc.disable is True


@pytest.mark.asyncio
async def test_gemini_code_status_is_classified_and_falls_back() -> None:
    calls: list[str] = []

    async def invoke(provider: EnabledProvider, schema: type[BaseModel], prompt: str) -> BaseModel:
        del prompt
        calls.append(provider.definition.name)
        if provider.definition.name == "gemini":
            raise GeminiHttpError(429)
        return schema.model_validate({"value": "ok"})

    settings = router_settings(
        llm_provider_order=("gemini", "groq"),
        gemini_api_key=SecretStr("gemini-secret"),
    )
    router = LLMRouter(settings, CircuitStore(), provider_invoker=invoke)
    async with routing_context(router) as stats:
        result = await router.invoke(ProbeResult, "safe input")

    assert result == ProbeResult(value="ok")
    assert calls == ["gemini", "groq"]
    assert stats.attempts[0].status == "rate_limited"


@pytest.mark.asyncio
async def test_unknown_provider_error_logs_sanitized_detail() -> None:
    secret = "groq-secret"

    async def invoke(provider: EnabledProvider, schema: type[BaseModel], prompt: str) -> BaseModel:
        del prompt
        if provider.definition.name == "groq":
            raise RuntimeError(f"SDK failed key={secret} donor=+923001234567")
        return schema.model_validate({"value": "ok"})

    with structlog.testing.capture_logs() as logs:
        result = await LLMRouter(router_settings(), CircuitStore(), provider_invoker=invoke).invoke(
            ProbeResult, "safe input"
        )

    rendered = repr(logs)
    assert result == ProbeResult(value="ok")
    assert secret not in rendered
    assert "+923001234567" not in rendered
    assert "+92300*****67" in rendered
    assert "SDK failed" in rendered


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
