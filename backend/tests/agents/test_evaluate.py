"""Evaluation CLI controls and diagnostic summary tests."""

from datetime import date
from typing import cast

import pytest

from app.agents import evaluate
from app.agents.evaluation_cases import EvaluationCase
from app.agents.graph import ReplyAgent
from app.agents.state import AgentExecution, AgentFailure, AgentResult, ProviderAttempt
from app.models.enums import ResponseIntent


class FakeEvaluationAgent:
    """Return configured executions in evaluation order."""

    def __init__(self, executions: list[AgentExecution]) -> None:
        self._executions = iter(executions)

    async def run_with_diagnostics(self, **kwargs: object) -> AgentExecution:
        del kwargs
        return next(self._executions)


def _execution(
    intent: ResponseIntent,
    *,
    failure: AgentFailure | None = None,
    provider: str | None = "groq",
) -> AgentExecution:
    attempts = (ProviderAttempt("groq", "openai/gpt-oss-20b", "answered"),) if provider else ()
    return AgentExecution(
        result=AgentResult(intent=intent, confidence=0.9, detected_language="en"),
        provider=provider,
        model="openai/gpt-oss-20b" if provider else None,
        fallback_count=0,
        attempts=attempts,
        failure=failure,
    )


def test_parse_evaluation_controls() -> None:
    options = evaluate.parse_args(["--delay-ms", "0", "--provider", "gemini"])

    assert options == evaluate.EvaluationOptions(delay_ms=0, provider="gemini")


@pytest.mark.asyncio
async def test_evaluation_separates_wrong_answers_from_provider_exhaustion(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cases = (
        EvaluationCase("Confirm", ResponseIntent.CONFIRM),
        EvaluationCase("Reschedule", ResponseIntent.RESCHEDULE, date_offset_days=7),
    )
    monkeypatch.setattr(evaluate, "EVALUATION_CASES", cases)
    agent = FakeEvaluationAgent(
        [
            _execution(ResponseIntent.QUESTION),
            _execution(
                ResponseIntent.UNKNOWN,
                failure="routing_unavailable",
                provider=None,
            ),
        ]
    )

    exit_code = await evaluate._evaluate_cases(
        cast(ReplyAgent, agent),
        date(2026, 10, 7),
        delay_ms=0,
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "01 WRONG" in output
    assert "02 NO_PROVIDER" in output
    assert "expected: intent=reschedule date=2026-10-14 reason=none slot=none" in output
    assert "attempts: groq:answered" in output
    assert "wrong_answer=1 no_provider_answered=1 agent_error=0" in output
