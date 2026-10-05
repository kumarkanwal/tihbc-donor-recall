"""Tests for deterministic auto-read selection."""

from uuid import UUID

from app.services.messaging.delivery import should_auto_read


def test_auto_read_selection_is_stable_and_honors_rate_edges() -> None:
    message_id = UUID(int=5_000)

    assert should_auto_read(message_id, 0.0) is False
    assert should_auto_read(message_id, 0.5) is False
    assert should_auto_read(message_id, 0.5001) is True
    assert should_auto_read(message_id, 1.0) is True
