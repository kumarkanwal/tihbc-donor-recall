"""Request-scoped composition for simulator query and write services."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_event_publisher
from app.core.clock import Clock, get_clock
from app.core.db import get_db
from app.repositories.donor import DonorRepository
from app.repositories.enrollment import EnrollmentRepository
from app.repositories.simulator_conversations import ConversationRepository
from app.repositories.simulator_messages import SimulatorMessageRepository
from app.services.events.base import EventPublisher
from app.services.simulator.query import SimulatorQueryService
from app.services.simulator.receipts import SimulatorReceiptService
from app.services.simulator.replies import SimulatorReplyService


def get_simulator_query_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SimulatorQueryService:
    """Build thread and cursor queries."""
    return SimulatorQueryService(
        DonorRepository(db), ConversationRepository(db), SimulatorMessageRepository(db)
    )


def get_simulator_receipt_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    publisher: Annotated[EventPublisher, Depends(get_event_publisher)],
    current_clock: Annotated[Clock, Depends(get_clock)],
) -> SimulatorReceiptService:
    """Build delivered-to-read transitions."""
    return SimulatorReceiptService(
        db, DonorRepository(db), SimulatorMessageRepository(db), publisher, current_clock
    )


def get_simulator_reply_service(
    db: Annotated[AsyncSession, Depends(get_db)],
    publisher: Annotated[EventPublisher, Depends(get_event_publisher)],
    current_clock: Annotated[Clock, Depends(get_clock)],
) -> SimulatorReplyService:
    """Build transactional reply capture."""
    return SimulatorReplyService(
        db,
        DonorRepository(db),
        SimulatorMessageRepository(db),
        EnrollmentRepository(db),
        publisher,
        current_clock,
    )
