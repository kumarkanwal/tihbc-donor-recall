"""Demo-clock API schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class DemoClockAdvance(BaseModel):
    """Non-negative whole-hour demo-clock advance."""

    days: int = Field(default=0, ge=0)
    hours: int = Field(default=0, ge=0)


class DemoClockOut(BaseModel):
    """Current demo time and durable offset."""

    now: datetime
    offset_seconds: int
