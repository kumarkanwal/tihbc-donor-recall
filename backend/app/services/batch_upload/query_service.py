"""Read imported donor batches and their donors."""

from uuid import UUID

from app.core.errors import NotFoundError
from app.core.logging import mask_phone_number
from app.models.enums import LanguageCode
from app.repositories.donor import DonorRepository
from app.repositories.donor_batch import BatchSummaryRecord, DonorBatchRepository
from app.schemas.donor_batch import (
    DonorBatchDetail,
    DonorBatchOut,
    DonorBatchPage,
    DonorOut,
    DonorPage,
    LanguageBreakdown,
    SegmentBreakdown,
    UploadedBySummary,
    ValidationIssue,
)


class DonorBatchQueryService:
    """Build API-safe views of imported batches and donors."""

    def __init__(
        self,
        batch_repository: DonorBatchRepository,
        donor_repository: DonorRepository,
    ) -> None:
        self._batches = batch_repository
        self._donors = donor_repository

    async def list_batches(
        self,
        *,
        search: str | None,
        sort: str,
        page: int,
        page_size: int,
    ) -> DonorBatchPage:
        """Return a searchable page of batch summaries."""
        result = await self._batches.list_with_summary(
            search=search,
            sort=sort,
            page=page,
            page_size=page_size,
        )
        return DonorBatchPage(
            items=[_batch_out(record) for record in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
        )

    async def get_batch(self, batch_id: UUID) -> DonorBatchDetail:
        """Return one batch with query-computed breakdowns."""
        record = await self._required_batch(batch_id)
        summary = _batch_out(record)
        segment_rows = await self._batches.segment_breakdown(batch_id)
        language_rows = await self._batches.language_breakdown(batch_id)
        return DonorBatchDetail(
            **summary.model_dump(),
            segment_breakdown=[
                SegmentBreakdown(segment=segment, count=count) for segment, count in segment_rows
            ],
            language_breakdown=[
                LanguageBreakdown(language=language, count=count)
                for language, count in language_rows
            ],
        )

    async def list_donors(
        self,
        batch_id: UUID,
        *,
        segment: str | None,
        language: LanguageCode | None,
        search: str | None,
        sort: str,
        page: int,
        page_size: int,
    ) -> DonorPage:
        """Return filtered donors with masked phone numbers."""
        await self._required_batch(batch_id)
        result = await self._donors.list_for_batch(
            batch_id,
            segment=segment,
            language=language,
            search=search,
            sort=sort,
            page=page,
            page_size=page_size,
        )
        return DonorPage(
            items=[
                DonorOut(
                    id=record.donor.id,
                    full_name=record.donor.full_name,
                    phone_e164=mask_phone_number(record.donor.phone_e164),
                    segment=record.segment_key,
                    language=record.donor.language,
                    city=record.donor.city,
                    blood_group=record.donor.blood_group,
                    last_donation_date=record.donor.last_donation_date,
                    created_at=record.donor.created_at,
                )
                for record in result.items
            ],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
        )

    async def validation_report(self, batch_id: UUID) -> list[ValidationIssue]:
        """Return the row errors persisted with a batch."""
        record = await self._required_batch(batch_id)
        return [ValidationIssue.model_validate(item) for item in record.batch.validation_report]

    async def _required_batch(self, batch_id: UUID) -> BatchSummaryRecord:
        record = await self._batches.get_with_summary(batch_id)
        if record is None:
            raise NotFoundError("Donor batch not found")
        return record


def _batch_out(record: BatchSummaryRecord) -> DonorBatchOut:
    batch = record.batch
    return DonorBatchOut(
        id=batch.id,
        name=batch.name,
        original_filename=batch.original_filename,
        total_rows=batch.total_rows,
        valid_rows=batch.valid_rows,
        invalid_rows=batch.invalid_rows,
        uploaded_by=UploadedBySummary(
            id=record.uploaded_by.id,
            full_name=record.uploaded_by.full_name,
        ),
        created_at=batch.created_at,
        campaign_count=record.campaign_count,
    )
