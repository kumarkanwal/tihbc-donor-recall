"""Donor and segment database queries."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.donor import Donor, DonorBatch, Segment
from app.models.enums import LanguageCode
from app.repositories.base import BaseRepository


@dataclass(frozen=True)
class DonorListRecord:
    """A donor paired with its segment key."""

    donor: Donor
    segment_key: str


@dataclass(frozen=True)
class DonorRecordPage:
    """One page of donor query records."""

    items: tuple[DonorListRecord, ...]
    total: int
    page: int
    page_size: int


class SegmentRepository(BaseRepository[Segment]):
    """Read donor segment reference data."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Segment)

    async def list_all(self) -> tuple[Segment, ...]:
        """Return all segments in deterministic key order."""
        result = await self._session.scalars(select(Segment).order_by(Segment.key))
        return tuple(result.all())


class DonorRepository(BaseRepository[Donor]):
    """Query and bulk-insert donors without applying upload rules."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Donor)

    async def add_many(self, donors: list[Donor]) -> tuple[Donor, ...]:
        """Add and flush a donor collection in the current transaction."""
        self._session.add_all(donors)
        await self._session.flush()
        return tuple(donors)

    async def existing_batch_names(self, phones: set[str]) -> dict[str, str]:
        """Map known phones to their most recently created batch name."""
        if not phones:
            return {}
        statement = (
            select(Donor.phone_e164, DonorBatch.name)
            .join(DonorBatch, Donor.batch_id == DonorBatch.id)
            .where(Donor.phone_e164.in_(phones))
            .order_by(DonorBatch.created_at.desc(), DonorBatch.id.desc())
        )
        rows = await self._session.execute(statement)
        existing: dict[str, str] = {}
        for phone, batch_name in rows:
            existing.setdefault(phone, batch_name)
        return existing

    async def list_for_batch(
        self,
        batch_id: UUID,
        *,
        segment: str | None,
        language: LanguageCode | None,
        search: str | None,
        sort: str,
        page: int,
        page_size: int,
    ) -> DonorRecordPage:
        """Return filtered donors and their segment keys."""
        filters = [Donor.batch_id == batch_id]
        if segment:
            filters.append(func.lower(Segment.key) == segment.strip().lower())
        if language:
            filters.append(Donor.language == language)
        if search and search.strip():
            term = f"%{search.strip()}%"
            filters.append(
                or_(
                    Donor.full_name.ilike(term),
                    Donor.phone_e164.ilike(term),
                    Donor.city.ilike(term),
                )
            )
        order_column = (
            Donor.full_name if sort.removeprefix("-") == "full_name" else Donor.created_at
        )
        order_by = order_column.desc() if sort.startswith("-") else order_column.asc()
        statement = (
            select(Donor, Segment.key)
            .join(Segment, Donor.segment_id == Segment.id)
            .where(*filters)
            .order_by(order_by, Donor.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        count_statement = (
            select(func.count())
            .select_from(Donor)
            .join(Segment, Donor.segment_id == Segment.id)
            .where(*filters)
        )
        rows = await self._session.execute(statement)
        total = await self._session.scalar(count_statement)
        return DonorRecordPage(
            items=tuple(
                DonorListRecord(donor=donor, segment_key=segment_key) for donor, segment_key in rows
            ),
            total=total or 0,
            page=page,
            page_size=page_size,
        )
