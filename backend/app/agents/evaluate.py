"""Run the non-CI multilingual evaluation set against configured providers."""

import asyncio
import sys
from datetime import UTC, date, datetime, time, timedelta
from time import perf_counter
from typing import Literal
from uuid import uuid4

from app.agents.evaluation_cases import EVALUATION_CASES, EvaluationCase
from app.agents.graph import ReplyAgent
from app.agents.llm.router import LLMRouter
from app.agents.state import AgentMetadata, AgentResult, OfferedSlot
from app.core.clock import clock
from app.core.config import Settings, get_settings
from app.core.db import create_database_resources
from app.core.redis import create_redis_client
from app.repositories.demo_clock import DatabaseClockPersistence


async def run_evaluation() -> int:
    """Execute all cases and print result, provider, latency, and accuracy."""
    settings = get_settings()
    if not settings.llm_enabled:
        sys.stderr.write("LLM_ENABLED must be true for the real-provider evaluation.\n")
        return 2
    redis = create_redis_client(settings.redis_url)
    database = create_database_resources(settings.database_url)
    try:
        await clock.initialize(DatabaseClockPersistence(database.session_factory))
        router = LLMRouter(settings, redis)
        await router.check_models()
        if not router.providers:
            sys.stderr.write("No provider API keys are configured.\n")
            return 2
        agent = _agent(router, settings)
        return await _evaluate_cases(agent, clock.now().date())
    finally:
        await redis.aclose()
        await database.engine.dispose()


def _agent(router: LLMRouter, settings: Settings) -> ReplyAgent:
    return ReplyAgent(
        router,
        confidence_threshold=settings.agent_confidence_threshold,
        tracing_enabled=settings.langsmith_tracing,
        langsmith_api_key=(
            settings.langsmith_api_key.get_secret_value()
            if settings.langsmith_api_key is not None
            else None
        ),
        langsmith_project=settings.langsmith_project,
        langsmith_endpoint=settings.langsmith_endpoint,
    )


async def _evaluate_cases(agent: ReplyAgent, today: date) -> int:
    slots = _offered_slots(today)
    passed = 0
    for index, case in enumerate(EVALUATION_CASES, start=1):
        started = perf_counter()
        execution = await agent.run_with_diagnostics(
            text=case.text,
            donor_language=_stored_language(case.text),
            awaiting=case.awaiting,
            offered_slots=slots,
            today=today,
            metadata=AgentMetadata(
                campaign_id=uuid4(),
                enrollment_id=uuid4(),
                donor_language=_stored_language(case.text),
                awaiting=case.awaiting,
                environment="evaluation",
            ),
        )
        latency_ms = (perf_counter() - started) * 1000
        correct = _matches(case, execution.result, today, slots)
        passed += int(correct)
        sys.stdout.write(
            f"{index:02d} {'PASS' if correct else 'FAIL'} "
            f"expected={case.expected_intent.value} actual={execution.result.intent.value} "
            f"provider={execution.provider or 'none'} latency_ms={latency_ms:.0f} "
            f"text={case.text!r}\n"
        )
    accuracy = passed / len(EVALUATION_CASES)
    sys.stdout.write(f"Accuracy: {passed}/{len(EVALUATION_CASES)} ({accuracy:.1%})\n")
    return 0 if passed == len(EVALUATION_CASES) else 1


def _matches(
    case: EvaluationCase,
    result: AgentResult,
    today: date,
    slots: list[OfferedSlot],
) -> bool:
    if result.intent != case.expected_intent:
        return False
    if case.expected_reason is not None and result.decline_reason != case.expected_reason:
        return False
    if case.date_offset_days is not None:
        return result.requested_date == today + timedelta(days=case.date_offset_days)
    if case.next_weekday is not None:
        return result.requested_date == _next_weekday(today, case.next_weekday)
    if case.selected_slot_index is not None:
        return result.selected_slot_id == slots[case.selected_slot_index].id
    return True


def _offered_slots(today: date) -> list[OfferedSlot]:
    dates = (today + timedelta(days=1), _next_weekday(today, 5), today + timedelta(days=7))
    return [
        OfferedSlot(
            id=uuid4(),
            starts_at=datetime.combine(slot_date, time(hour=10), UTC),
            center_name="Korangi Campus Blood Center",
            label=slot_date.strftime("%A %d %b, 10:00 AM"),
        )
        for slot_date in dates
    ]


def _next_weekday(today: date, weekday: int) -> date:
    days = (weekday - today.weekday()) % 7
    return today + timedelta(days=days or 7)


def _stored_language(text: str) -> Literal["en", "ur"]:
    return "ur" if any("\u0600" <= char <= "\u06ff" for char in text) else "en"


def main() -> None:
    """CLI entry point."""
    raise SystemExit(asyncio.run(run_evaluation()))


if __name__ == "__main__":
    main()
