"""Content-series step mutation business logic."""

from uuid import UUID

from app.core.errors import ValidationError
from app.models.enums import MediaType
from app.models.series import SeriesStep, SeriesStepContent
from app.schemas.content_series import (
    ContentSeriesDetail,
    QuickReplyButtonInput,
    SeriesReorderInput,
    SeriesStepContentInput,
    SeriesStepInput,
    SeriesStepOut,
    SeriesStepUpdate,
)
from app.services.content_series.access import ContentSeriesAccess
from app.services.content_series.mappers import series_detail, step_out
from app.services.content_series.validation import validate_step_values


class SeriesStepService:
    """Create, update, delete, and reorder series steps."""

    def __init__(self, access: ContentSeriesAccess) -> None:
        self._access = access

    async def create_step(self, series_id: UUID, request: SeriesStepInput) -> SeriesStepOut:
        """Append one step to an editable series."""
        series = await self._access.editable(series_id)
        validate_step_values(series.languages, request.contents, request.buttons)
        step = self._new_step(request, len(series.steps) + 1)
        series.steps.append(step)
        self._access.ensure_active_valid(series)
        await self._access.commit()
        refreshed = await self._access.reload(series_id)
        return step_out(self._access.step_by_id(refreshed, step.id))

    async def update_step(
        self,
        series_id: UUID,
        step_id: UUID,
        request: SeriesStepUpdate,
    ) -> SeriesStepOut:
        """Update one step while preserving its order."""
        series = await self._access.editable(series_id)
        step = self._access.step_by_id(series, step_id)
        contents = request.contents if request.contents is not None else self._content_inputs(step)
        buttons = request.buttons if request.buttons is not None else self._button_inputs(step)
        validate_step_values(series.languages, contents, buttons)
        self._apply_step_update(step, request)
        self._access.ensure_active_valid(series)
        await self._access.commit()
        refreshed = await self._access.reload(series_id)
        return step_out(self._access.step_by_id(refreshed, step_id))

    async def delete_step(self, series_id: UUID, step_id: UUID) -> ContentSeriesDetail:
        """Delete a step and renumber all remaining steps."""
        series = await self._access.editable(series_id)
        step = self._access.step_by_id(series, step_id)
        series.steps.remove(step)
        await self._access.session.delete(step)
        await self._access.session.flush()
        ordered_ids = [item.id for item in sorted(series.steps, key=lambda item: item.step_order)]
        if ordered_ids:
            await self._access.repository.reorder_steps(series_id, ordered_ids)
        self._access.ensure_active_valid(series)
        await self._access.commit()
        return series_detail(await self._access.reload(series_id))

    async def reorder_steps(
        self, series_id: UUID, request: SeriesReorderInput
    ) -> ContentSeriesDetail:
        """Apply a complete contiguous order to all series steps."""
        series = await self._access.editable(series_id)
        existing_ids = {step.id for step in series.steps}
        if set(request.step_ids) != existing_ids or len(request.step_ids) != len(series.steps):
            raise ValidationError("Reorder must contain every series step exactly once")
        await self._access.repository.reorder_steps(series_id, request.step_ids)
        self._access.ensure_active_valid(series)
        await self._access.commit()
        return series_detail(await self._access.reload(series_id))

    @staticmethod
    def _new_step(request: SeriesStepInput, order: int) -> SeriesStep:
        return SeriesStep(
            step_order=order,
            delay_days=request.delay_days,
            category=request.category,
            media_type=request.media_type,
            media_url=request.media_url if request.media_type != MediaType.NONE else None,
            buttons=[button.model_dump(mode="json") for button in request.buttons],
            contents=[
                SeriesStepContent(language=item.language, body=item.body)
                for item in request.contents
            ],
        )

    @staticmethod
    def _apply_step_update(step: SeriesStep, request: SeriesStepUpdate) -> None:
        if request.delay_days is not None:
            step.delay_days = request.delay_days
        if request.category is not None:
            step.category = request.category
        if request.media_type is not None:
            step.media_type = request.media_type
        if "media_url" in request.model_fields_set:
            step.media_url = request.media_url
        if step.media_type == MediaType.NONE:
            step.media_url = None
        if request.contents is not None:
            SeriesStepService._replace_contents(step, request.contents)
        if request.buttons is not None:
            step.buttons = [button.model_dump(mode="json") for button in request.buttons]

    @staticmethod
    def _content_inputs(step: SeriesStep) -> list[SeriesStepContentInput]:
        return [
            SeriesStepContentInput(language=item.language, body=item.body) for item in step.contents
        ]

    @staticmethod
    def _button_inputs(step: SeriesStep) -> list[QuickReplyButtonInput]:
        return [QuickReplyButtonInput.model_validate(item) for item in step.buttons]

    @staticmethod
    def _replace_contents(step: SeriesStep, contents: list[SeriesStepContentInput]) -> None:
        replacements = {item.language: item.body for item in contents}
        for existing in tuple(step.contents):
            body = replacements.pop(existing.language, None)
            if body is None:
                step.contents.remove(existing)
            else:
                existing.body = body
        step.contents.extend(
            SeriesStepContent(language=language, body=body)
            for language, body in replacements.items()
        )
