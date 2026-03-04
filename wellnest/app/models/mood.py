from __future__ import annotations

from datetime import date, datetime
from pydantic import BaseModel, Field


class MoodLogCreate(BaseModel):
    date: date
    mood_score: int = Field(ge=1, le=10, description="Mood score from 1 (worst) to 10 (best)")
    notes: str | None = Field(default=None, max_length=2000)


class MoodLogResponse(BaseModel):
    id: str
    user_id: str
    date: date
    mood_score: int
    notes: str | None
    created_at: datetime
    updated_at: datetime | None = None


class MoodTrendPoint(BaseModel):
    date: date
    mood_score: int


class MoodTrendsResponse(BaseModel):
    points: list[MoodTrendPoint]
    avg_7d: float | None = None