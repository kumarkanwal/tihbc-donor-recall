"""Configured messaging-provider factory."""

from app.messaging.base import MessagingProvider
from app.messaging.simulator import SimulatorProvider


def create_messaging_provider(provider_name: str) -> MessagingProvider:
    """Create the configured provider or reject an unsupported name."""
    if provider_name == "simulator":
        return SimulatorProvider()
    raise ValueError(f"Unsupported messaging provider: {provider_name}")
