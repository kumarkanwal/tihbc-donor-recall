"""Structured LLM routing with bounded fallback and Redis circuit state."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from time import monotonic

import httpx
import structlog
from google.genai.types import AutomaticFunctionCallingConfig
from langchain_core.runnables import Runnable, RunnableLambda
from pydantic import BaseModel
from redis.asyncio import Redis

from app.agents.llm.circuit import CircuitBreaker, CircuitStore
from app.agents.llm.diagnostics import (
    provider_attempt_status,
    provider_status_code,
    safe_provider_error_detail,
)
from app.agents.llm.discovery import model_available
from app.agents.llm.providers import (
    EnabledProvider,
    create_chat_model,
    enabled_providers,
    structured_output_strict,
)
from app.agents.state import ProviderAttempt, ProviderAttemptStatus
from app.core.config import Settings

logger = structlog.get_logger(__name__)
UNAVAILABLE_PROVIDER_COOLDOWN_MULTIPLIER = 10
GEMINI_AFC_DISABLED = AutomaticFunctionCallingConfig(disable=True)


class RetryableProviderError(RuntimeError):
    """A provider failure eligible for the next configured fallback."""


class RoutingUnavailable(RuntimeError):
    """No provider produced a valid result within the routing budget."""


@dataclass
class RouteStats:
    """Per-agent-run routing diagnostics for tracing and evaluation."""

    provider: str | None = None
    model: str | None = None
    fallback_count: int = 0
    attempts: list[ProviderAttempt] = field(default_factory=list)


ProviderInvoker = Callable[[EnabledProvider, type[BaseModel], str], Awaitable[BaseModel]]
_active_router: ContextVar[LLMRouter | None] = ContextVar("active_llm_router", default=None)
_route_stats: ContextVar[RouteStats | None] = ContextVar("llm_route_stats", default=None)


class RoutedStructuredLLM[SchemaT: BaseModel]:
    """Schema-bound entry point returned to graph nodes."""

    def __init__(self, router: LLMRouter, schema: type[SchemaT]) -> None:
        self._router = router
        self._schema = schema

    async def ainvoke(self, prompt: str) -> SchemaT:
        """Invoke the ordered provider chain and validate the schema."""
        result = await self._router.invoke(self._schema, prompt)
        return self._schema.model_validate(result)


class LLMRouter:
    """Route structured calls through enabled providers with shared circuit state."""

    def __init__(
        self,
        settings: Settings,
        redis: Redis | CircuitStore,
        *,
        provider_invoker: ProviderInvoker | None = None,
    ) -> None:
        self._settings = settings
        self._circuit = CircuitBreaker(
            redis,
            failure_threshold=settings.llm_circuit_failures,
            cooldown_seconds=settings.llm_circuit_cooldown_seconds,
        )
        self._providers = enabled_providers(settings)
        self._provider_invoker = provider_invoker or self._invoke_langchain
        self._unavailable: set[str] = set()

    @property
    def providers(self) -> tuple[EnabledProvider, ...]:
        """Return enabled providers in configured order without their secret values."""
        return self._providers

    async def check_models(self) -> None:
        """Validate configured model IDs without making startup fatal."""
        active: list[str] = []
        async with httpx.AsyncClient(timeout=self._settings.llm_timeout_seconds) as client:
            for provider in self._providers:
                if await model_available(client, provider):
                    active.append(provider.definition.name)
                else:
                    self._unavailable.add(provider.definition.name)
        logger.info("llm_providers_ready", providers=active)

    def get_structured_llm[SchemaT: BaseModel](
        self, schema: type[SchemaT]
    ) -> RoutedStructuredLLM[SchemaT]:
        """Bind one Pydantic output schema to this router."""
        return RoutedStructuredLLM(self, schema)

    async def invoke(self, schema: type[BaseModel], prompt: str) -> BaseModel:
        """Execute one LangChain fallback chain within the total time budget."""
        providers = tuple(
            provider
            for provider in self._providers
            if provider.definition.name not in self._unavailable
        )
        if not providers:
            raise RoutingUnavailable("No enabled LLM provider is available")
        deadline = monotonic() + self._settings.llm_total_budget_seconds
        runnables = tuple(
            self._provider_runnable(provider, schema, deadline) for provider in providers
        )
        chain = runnables[0].with_fallbacks(
            list(runnables[1:]), exceptions_to_handle=(RetryableProviderError,)
        )
        try:
            async with asyncio.timeout(self._settings.llm_total_budget_seconds):
                return await chain.ainvoke(prompt)
        except (TimeoutError, RetryableProviderError) as error:
            raise RoutingUnavailable("LLM routing budget or providers exhausted") from error

    def _provider_runnable(
        self,
        provider: EnabledProvider,
        schema: type[BaseModel],
        deadline: float,
    ) -> Runnable[str, BaseModel]:
        async def call(prompt: str) -> BaseModel:
            return await self._call_provider(provider, schema, prompt, deadline)

        return RunnableLambda(call)

    async def _call_provider(
        self,
        provider: EnabledProvider,
        schema: type[BaseModel],
        prompt: str,
        deadline: float,
    ) -> BaseModel:
        name = provider.definition.name
        if await self._circuit.is_open(name):
            self._stats().fallback_count += 1
            self._record_attempt(provider, "circuit_open")
            raise RetryableProviderError(f"Provider circuit is open: {name}")
        remaining = deadline - monotonic()
        if remaining <= 0:
            self._stats().fallback_count += 1
            self._record_attempt(provider, "budget_exhausted")
            raise RetryableProviderError("LLM total budget exhausted")
        try:
            async with asyncio.timeout(min(self._settings.llm_timeout_seconds, remaining)):
                result = await self._provider_invoker(provider, schema, prompt)
                validated = schema.model_validate(result)
        except Exception as error:
            await self._handle_failure(provider, error)
            raise AssertionError("failure handler always raises") from error
        await self._circuit.reset(name)
        stats = self._stats()
        stats.provider, stats.model = name, provider.model
        self._record_attempt(provider, "answered")
        return validated

    async def _handle_failure(self, provider: EnabledProvider, error: Exception) -> None:
        name = provider.definition.name
        status = provider_status_code(error)
        attempt_status = provider_attempt_status(error, status)
        self._stats().fallback_count += 1
        self._record_attempt(provider, attempt_status, status)
        if status in {400, 401, 402, 403}:
            multiplier = (
                UNAVAILABLE_PROVIDER_COOLDOWN_MULTIPLIER if status in {401, 402, 403} else 1
            )
            await self._circuit.open(
                name,
                cooldown_seconds=self._settings.llm_circuit_cooldown_seconds * multiplier,
            )
            log = logger.warning if status == 400 else logger.error
            log(
                "llm_provider_unavailable",
                provider=name,
                status=status,
                error_detail=safe_provider_error_detail(error, provider.api_key.get_secret_value()),
                error_type=type(error).__name__,
            )
        else:
            await self._circuit.record_failure(name)
            logger.warning(
                "llm_provider_fallback",
                provider=name,
                status=status,
                failure=attempt_status,
                error_detail=safe_provider_error_detail(error, provider.api_key.get_secret_value()),
                error_type=type(error).__name__,
            )
        raise RetryableProviderError(f"Provider failed: {name}") from error

    async def _invoke_langchain(
        self, provider: EnabledProvider, schema: type[BaseModel], prompt: str
    ) -> BaseModel:
        model = create_chat_model(provider, self._settings)
        structured = model.with_structured_output(
            schema,
            method="json_schema",
            strict=structured_output_strict(provider),
        )
        if provider.definition.client_type == "gemini":
            structured = structured.bind(automatic_function_calling=GEMINI_AFC_DISABLED)
        result = await structured.ainvoke(prompt)
        return schema.model_validate(result)

    def _record_attempt(
        self,
        provider: EnabledProvider,
        status: ProviderAttemptStatus,
        http_status: int | None = None,
    ) -> None:
        self._stats().attempts.append(
            ProviderAttempt(
                provider=provider.definition.name,
                model=provider.model,
                status=status,
                http_status=http_status,
            )
        )

    @staticmethod
    def _stats() -> RouteStats:
        stats = _route_stats.get()
        if stats is None:
            stats = RouteStats()
            _route_stats.set(stats)
        return stats


def get_structured_llm[SchemaT: BaseModel](
    schema: type[SchemaT],
) -> RoutedStructuredLLM[SchemaT]:
    """Return the schema-bound LLM for the active agent execution."""
    router = _active_router.get()
    if router is None:
        raise RoutingUnavailable("No LLM router is bound to this execution")
    return router.get_structured_llm(schema)


@asynccontextmanager
async def routing_context(router: LLMRouter) -> AsyncIterator[RouteStats]:
    """Bind a router and isolated stats to one asynchronous graph run."""
    router_token = _active_router.set(router)
    stats_token = _route_stats.set(RouteStats())
    try:
        yield LLMRouter._stats()
    finally:
        _route_stats.reset(stats_token)
        _active_router.reset(router_token)
