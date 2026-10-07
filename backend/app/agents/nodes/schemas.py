"""Strict JSON-schema base for provider structured outputs."""

from pydantic import BaseModel, ConfigDict


class StrictOutputModel(BaseModel):
    """Forbid undeclared fields so constrained decoders can enforce the schema."""

    model_config = ConfigDict(extra="forbid")
