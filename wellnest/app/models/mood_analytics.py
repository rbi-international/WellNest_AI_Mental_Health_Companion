from __future__ import annotations

from datetime import date
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field


class MetricExplanation(BaseModel):
    name: str
    value: Optional[float] = None
    interpretation: str
    evidence: Dict[str, Any] = Field(default_factory=dict)


class MoodAnalyticsResponse(BaseModel):
    user_id: str

    window_start: date
    window_end: date

    n_observations: int = Field(ge=0)
    coverage_ratio: float = Field(ge=0.0, le=1.0)

    mood_stability_index: float = Field(ge=0.0, le=1.0)
    mood_volatility_index: float = Field(ge=0.0, le=1.0)
    mood_trend_score: float = Field(ge=-1.0, le=1.0)
    low_mood_persistence: float = Field(ge=0.0, le=1.0)
    recovery_resilience_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)

    composite_risk_signal: float = Field(ge=0.0, le=1.0)
    attention_level: str  # "low" | "moderate" | "high"

    safe_summary: str

    explanations: List[MetricExplanation] = Field(default_factory=list)