"""Login and observe public events from the local API."""

import argparse
import asyncio
from getpass import getpass
from urllib.parse import urlencode, urlsplit, urlunsplit

import httpx
import structlog
from websockets.asyncio.client import connect

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.ws.events import EventEnvelope

logger = structlog.get_logger(__name__)


async def listen(base_url: str, email: str, password: str) -> None:
    """Login without logging credentials, then record received public events."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url.rstrip('/')}/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        response.raise_for_status()
        token = response.json()["access_token"]
    parts = urlsplit(base_url)
    endpoint = urlunsplit(
        (
            "wss" if parts.scheme == "https" else "ws",
            parts.netloc,
            "/ws",
            urlencode({"token": token}),
            "",
        )
    )
    async with connect(endpoint) as socket:
        logger.info("websocket_listener_connected")
        async for data in socket:
            event = EventEnvelope.model_validate_json(data).public()
            payload = event.payload.copy()
            if "body" in payload:
                payload["body"] = "[message body omitted]"
            logger.info(
                "websocket_event_received",
                type=event.type.value,
                ts=event.ts.isoformat(),
                payload=payload,
            )


def main() -> None:
    """Parse the API address and prompt for credentials securely."""
    settings = get_settings()
    configure_logging(settings.log_level)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument(
        "--email", default=settings.seed_admin_email, required=settings.seed_admin_email is None
    )
    arguments = parser.parse_args()
    asyncio.run(listen(arguments.url, arguments.email, getpass("Password: ")))


if __name__ == "__main__":
    main()
