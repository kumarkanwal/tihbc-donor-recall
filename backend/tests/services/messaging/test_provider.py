"""Tests for provider selection and simulator acceptance."""

from uuid import uuid4

import pytest

from app.messaging.base import OutboundButton
from app.messaging.factory import create_messaging_provider
from app.messaging.simulator import SimulatorProvider
from app.models.enums import MediaType


@pytest.mark.asyncio
async def test_factory_builds_simulator_provider() -> None:
    message_id = uuid4()
    provider = create_messaging_provider("simulator")

    result = await provider.send_template_message(
        message_id=message_id,
        recipient="+923001234567",
        body="Test",
        media_type=MediaType.NONE,
        media_url=None,
    )

    assert isinstance(provider, SimulatorProvider)
    assert result.provider_message_id == f"sim-{message_id}"

    text_result = await provider.send_text_message(
        message_id=message_id,
        recipient="+923001234567",
        body="Test",
    )
    interactive_result = await provider.send_interactive_message(
        message_id=message_id,
        recipient="+923001234567",
        body="Test",
        buttons=(OutboundButton(id="confirm", label="Confirm"),),
        media_type=MediaType.NONE,
        media_url=None,
    )
    assert text_result == result
    assert interactive_result == result


def test_factory_rejects_unknown_provider() -> None:
    with pytest.raises(ValueError, match="Unsupported messaging provider"):
        create_messaging_provider("unknown")
