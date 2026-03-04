from pydantic import BaseModel


class MoodAnalyticsResponse(BaseModel):

    average_mood: float

    trend_slope: float

    volatility_index: float

    interpretation: str