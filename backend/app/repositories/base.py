"""Generic database access shared by domain repositories."""

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base


@dataclass(frozen=True)
class Page[ModelType: Base]:
    """One page of model instances and its pagination metadata."""

    items: tuple[ModelType, ...]
    total: int
    page: int
    page_size: int


class BaseRepository[ModelType: Base]:
    """Provide common persistence operations without domain rules."""

    def __init__(self, session: AsyncSession, model_type: type[ModelType]) -> None:
        self._session = session
        self._model_type = model_type

    async def get(self, entity_id: UUID | int) -> ModelType | None:
        """Return one entity by primary key, if present."""
        return await self._session.get(self._model_type, entity_id)

    async def list(self, *, page: int = 1, page_size: int = 20) -> Page[ModelType]:
        """Return a deterministic page and total row count."""
        primary_key = inspect(self._model_type).primary_key[0]
        statement = (
            select(self._model_type)
            .order_by(primary_key)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await self._session.execute(statement)
        total = await self._session.scalar(select(func.count()).select_from(self._model_type))
        return Page(
            items=tuple(result.scalars().all()),
            total=total or 0,
            page=page,
            page_size=page_size,
        )

    async def add(self, entity: ModelType) -> ModelType:
        """Add and flush an entity without committing its transaction."""
        self._session.add(entity)
        await self._session.flush()
        return entity
