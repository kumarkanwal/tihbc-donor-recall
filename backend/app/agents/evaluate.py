"""Run the non-CI multilingual evaluation set against configured providers."""

import argparse
import asyncio
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from time import perf_counter
from typing import Literal
from uuid import uuid4

from app.agents.evaluation_cases import EVALUATION_CASES, EvaluationCase
from app.agents.graph import ReplyAgent
from app.agents.llm.providers import PROVIDERS
from app.agents.llm.router import LLMRouter
from app.agents.state import AgentExecution, AgentMetadata, AgentResult, OfferedSlot
from app.core.clock import clock
from app.core.config import Settings, get_settings
from app.core.db import create_database_resources
from app.core.redis import create_redis_client
from app.repositories.demo_clock import DatabaseClockPersistence

DEFAULT_DELAY_MS = 1500


@dataclass(frozen=True)
class EvaluationOptions:
    """Command-line controls for real-provider evaluation."""

    delay_ms: int = DEFAULT_DELAY_MS
    provider: str | None = None


async def run_evaluation(options: EvaluationOptions | None = None) -> int:
    """Execute all cases and print result, provider, latency, and accuracy."""
    options = options or EvaluationOptions()
    settings = get_settings()
    if not settings.llm_enabled:
        sys.stderr.write("LLM_ENABLED must be true for the real-provider evaluation.\n")
        return 2
    if options.provider is not None:
        settings = settings.model_copy(update={"llm_provider_order": (options.provider,)})
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
        return await _evaluate_cases(agent, clock.now().date(), options.delay_ms)
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


async def _evaluate_cases(agent: ReplyAgent, today: date, delay_ms: int) -> int:
    slots = _offered_slots(today)
    passed = 0
    wrong_answers = 0
    no_provider_answers = 0
    agent_errors = 0
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
        outcome = _outcome(correct, execution)
        wrong_answers += int(outcome == "WRONG")
        no_provider_answers += int(outcome == "NO_PROVIDER")
        agent_errors += int(outcome == "ERROR")
        sys.stdout.write(
            f"{index:02d} {outcome} text={case.text!r}\n"
            f"   expected: {_format_expected(case, today)}\n"
            f"   actual:   {_format_actual(execution.result, slots)}\n"
            f"   attempts: {_format_attempts(execution)}\n"
            f"   final_provider={execution.provider or 'none'} latency_ms={latency_ms:.0f}\n"
        )
        if index < len(EVALUATION_CASES) and delay_ms > 0:
            await asyncio.sleep(delay_ms / 1000)
    accuracy = passed / len(EVALUATION_CASES)
    sys.stdout.write(
        f"Summary: passed={passed}/{len(EVALUATION_CASES)} ({accuracy:.1%}) "
        f"wrong_answer={wrong_answers} no_provider_answered={no_provider_answers} "
        f"agent_error={agent_errors}\n"
    )
    return 0 if passed == len(EVALUATION_CASES) else 1


def _outcome(correct: bool, execution: AgentExecution) -> str:
    if correct:
        return "PASS"
    if execution.failure == "routing_unavailable":
        return "NO_PROVIDER"
    if execution.failure == "agent_error":
        return "ERROR"
    return "WRONG"


def _format_expected(case: EvaluationCase, today: date) -> str:
    requested_date = None
    if case.date_offset_days is not None:
        requested_date = today + timedelta(days=case.date_offset_days)
    elif case.next_weekday is not None:
        requested_date = _next_weekday(today, case.next_weekday)
    slot = case.selected_slot_index + 1 if case.selected_slot_index is not None else None
    return _format_fields(case.expected_intent.value, requested_date, case.expected_reason, slot)


def _format_actual(result: AgentResult, slots: list[OfferedSlot]) -> str:
    slot_lookup = {slot.id: index for index, slot in enumerate(slots, start=1)}
    slot: int | str | None = None
    if result.selected_slot_id is not None:
        slot = slot_lookup.get(result.selected_slot_id, str(result.selected_slot_id))
    return _format_fields(
        result.intent.value,
        result.requested_date,
        result.decline_reason,
        slot,
    )


def _format_fields(intent: str, requested_date: object, reason: object, slot: object) -> str:
    return (
        f"intent={intent} date={requested_date or 'none'} "
        f"reason={getattr(reason, 'value', None) or 'none'} slot={slot or 'none'}"
    )


def _format_attempts(execution: AgentExecution) -> str:
    if not execution.attempts:
        return "none"
    attempts = []
    for attempt in execution.attempts:
        status: str = attempt.status
        if attempt.http_status is not None:
            status = f"{status}({attempt.http_status})"
        attempts.append(f"{attempt.provider}:{status}")
    return " -> ".join(attempts)


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


def parse_args(argv: Sequence[str] | None = None) -> EvaluationOptions:
    """Parse safe evaluation controls without changing application settings."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--delay-ms",
        type=_non_negative_int,
        default=DEFAULT_DELAY_MS,
        help="Delay between cases in milliseconds (default: 1500).",
    )
    parser.add_argument(
        "--provider",
        choices=tuple(PROVIDERS),
        help="Evaluate only one configured provider.",
    )
    arguments = parser.parse_args(argv)
    return EvaluationOptions(delay_ms=arguments.delay_ms, provider=arguments.provider)


def _non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be zero or greater")
    return parsed


def main() -> None:
    """CLI entry point."""
    raise SystemExit(asyncio.run(run_evaluation(parse_args())))


if __name__ == "__main__":
    main()
