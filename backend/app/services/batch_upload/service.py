"""Orchestrate donor batch preview validation and transactional import."""

from collections import Counter

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.clock import Clock
from app.core.errors import ValidationError
from app.core.logging import mask_phone_number
from app.models.donor import Donor, DonorBatch, Segment
from app.repositories.donor import DonorRepository, SegmentRepository
from app.repositories.donor_batch import DonorBatchRepository
from app.schemas.donor_batch import (
    BatchImportRequest,
    BatchPreview,
    DonorBatchOut,
    DonorPreviewRow,
    ExistingPhoneWarning,
    LanguageBreakdown,
    SegmentBreakdown,
    StoredBatchPreview,
    StoredDonorRow,
    UploadedBySummary,
    ValidationIssue,
)
from app.schemas.user import UserOut
from app.services.batch_upload.parser import ParsedUpload, parse_upload
from app.services.batch_upload.preview_store import PreviewStore
from app.services.batch_upload.validators import (
    SegmentValue,
    find_duplicate_phone_rows,
    validate_row,
)

logger = structlog.get_logger(__name__)
PREVIEW_SAMPLE_SIZE = 10


class BatchUploadService:
    """Validate uploads and persist confirmed valid donors."""

    def __init__(
        self,
        session: AsyncSession,
        batch_repository: DonorBatchRepository,
        donor_repository: DonorRepository,
        segment_repository: SegmentRepository,
        preview_store: PreviewStore,
        current_clock: Clock,
        *,
        max_size_mb: int,
        max_rows: int,
    ) -> None:
        self._session = session
        self._batches = batch_repository
        self._donors = donor_repository
        self._segments = segment_repository
        self._previews = preview_store
        self._clock = current_clock
        self._max_size_mb = max_size_mb
        self._max_rows = max_rows

    async def preview(self, filename: str, content: bytes) -> BatchPreview:
        """Parse, validate, warn, and temporarily store an upload."""
        parsed = parse_upload(
            filename,
            content,
            max_size_mb=self._max_size_mb,
            max_rows=self._max_rows,
        )
        segments = await self._segments.list_all()
        donors, errors = self._validate_rows(parsed, segments)
        warnings = await self._existing_phone_warnings(donors)
        segment_breakdown, language_breakdown = _preview_breakdowns(donors)
        stored = StoredBatchPreview(
            original_filename=parsed.original_filename,
            total_rows=len(parsed.rows),
            valid_rows=len(donors),
            invalid_rows=len({error.row for error in errors}),
            donors=donors,
            segment_breakdown=segment_breakdown,
            language_breakdown=language_breakdown,
            errors=errors,
            warnings=warnings,
            expires_at=self._previews.expires_at(),
        )
        token = await self._previews.save(stored)
        logger.info(
            "donor_batch_previewed",
            total_rows=stored.total_rows,
            valid_rows=stored.valid_rows,
            invalid_rows=stored.invalid_rows,
            warning_count=len(stored.warnings),
        )
        return _preview_response(token, stored)

    async def import_batch(
        self,
        request: BatchImportRequest,
        uploaded_by: UserOut,
    ) -> DonorBatchOut:
        """Import one preview atomically and consume its token after commit."""
        preview = await self._previews.get(request.preview_token)
        if preview.valid_rows == 0:
            raise ValidationError("No valid donors to import")
        batch = DonorBatch(
            name=request.name.strip(),
            original_filename=preview.original_filename,
            uploaded_by_id=uploaded_by.id,
            total_rows=preview.total_rows,
            valid_rows=preview.valid_rows,
            invalid_rows=preview.invalid_rows,
            validation_report=[issue.model_dump(mode="json") for issue in preview.errors],
        )
        try:
            await self._batches.add(batch)
            await self._donors.add_many([_donor_model(batch, row) for row in preview.donors])
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
        await self._previews.delete(request.preview_token)
        logger.info(
            "donor_batch_imported",
            batch_id=str(batch.id),
            total_rows=batch.total_rows,
            valid_rows=batch.valid_rows,
            invalid_rows=batch.invalid_rows,
        )
        return DonorBatchOut(
            id=batch.id,
            name=batch.name,
            original_filename=batch.original_filename,
            total_rows=batch.total_rows,
            valid_rows=batch.valid_rows,
            invalid_rows=batch.invalid_rows,
            uploaded_by=UploadedBySummary(id=uploaded_by.id, full_name=uploaded_by.full_name),
            created_at=batch.created_at,
            campaign_count=0,
        )

    def _validate_rows(
        self,
        parsed: ParsedUpload,
        segments: tuple[Segment, ...],
    ) -> tuple[list[StoredDonorRow], list[ValidationIssue]]:
        segment_lookup = _segment_lookup(segments)
        duplicate_phone_rows = find_duplicate_phone_rows(parsed.rows)
        donors: list[StoredDonorRow] = []
        errors: list[ValidationIssue] = []
        for parsed_row in parsed.rows:
            donor, row_errors = validate_row(
                parsed_row,
                segments=segment_lookup,
                duplicate_phone_rows=duplicate_phone_rows,
                today=self._clock.now().date(),
            )
            errors.extend(row_errors)
            if donor is not None:
                donors.append(donor)
        return donors, errors

    async def _existing_phone_warnings(
        self, donors: list[StoredDonorRow]
    ) -> list[ExistingPhoneWarning]:
        existing = await self._donors.existing_batch_names({donor.phone for donor in donors})
        return [
            ExistingPhoneWarning(
                row=donor.row,
                phone=mask_phone_number(donor.phone),
                existing_batch_name=existing[donor.phone],
            )
            for donor in donors
            if donor.phone in existing
        ]


def _segment_lookup(segments: tuple[Segment, ...]) -> dict[str, SegmentValue]:
    lookup: dict[str, SegmentValue] = {}
    for segment in segments:
        value = SegmentValue(id=segment.id, key=segment.key)
        lookup[segment.key.casefold()] = value
        lookup[segment.label.casefold()] = value
    return lookup


def _preview_breakdowns(
    donors: list[StoredDonorRow],
) -> tuple[list[SegmentBreakdown], list[LanguageBreakdown]]:
    segments = Counter(donor.segment for donor in donors)
    languages = Counter(donor.language for donor in donors)
    return (
        [SegmentBreakdown(segment=key, count=count) for key, count in sorted(segments.items())],
        [LanguageBreakdown(language=key, count=count) for key, count in sorted(languages.items())],
    )


def _preview_response(token: str, stored: StoredBatchPreview) -> BatchPreview:
    return BatchPreview(
        preview_token=token,
        original_filename=stored.original_filename,
        total_rows=stored.total_rows,
        valid_rows=stored.valid_rows,
        invalid_rows=stored.invalid_rows,
        segment_breakdown=stored.segment_breakdown,
        language_breakdown=stored.language_breakdown,
        sample_valid_rows=[
            DonorPreviewRow.model_validate(row.model_dump(exclude={"segment_id"}))
            for row in stored.donors[:PREVIEW_SAMPLE_SIZE]
        ],
        errors=stored.errors,
        warnings=stored.warnings,
    )


def _donor_model(batch: DonorBatch, row: StoredDonorRow) -> Donor:
    return Donor(
        batch_id=batch.id,
        full_name=row.name,
        phone_e164=row.phone,
        segment_id=row.segment_id,
        language=row.language,
        city=row.city,
        blood_group=row.blood_group,
        last_donation_date=row.last_donation_date,
        sim_reachable=True,
        sim_read_receipts=True,
    )
