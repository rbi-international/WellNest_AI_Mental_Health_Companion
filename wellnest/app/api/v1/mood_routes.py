from __future__ import annotations

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_current_user
from app.models.mood import MoodLogCreate, MoodLogResponse, MoodTrendPoint, MoodTrendsResponse
from app.repositories.mood_repo import MoodRepository

router = APIRouter(prefix="/mood", tags=["mood"])
repo = MoodRepository()


def _to_response(doc) -> MoodLogResponse:
    return MoodLogResponse(
        id=str(doc["_id"]),
        user_id=doc["user_id"],
        date=date.fromisoformat(doc["date"]),
        mood_score=doc["mood_score"],
        notes=doc.get("notes"),
        created_at=doc["created_at"],
        updated_at=doc.get("updated_at"),
    )


@router.post("", response_model=MoodLogResponse)
async def log_mood(payload: MoodLogCreate, current_user=Depends(get_current_user)):
    user_id = str(current_user["_id"])

    doc = await repo.upsert_daily_mood(
        user_id=user_id,
        day=payload.date,
        mood_score=payload.mood_score,
        notes=payload.notes,
    )

    if not doc:
        raise HTTPException(status_code=500, detail="Failed to save mood log")

    return _to_response(doc)


@router.get("", response_model=list[MoodLogResponse])
async def list_mood_history(
    limit: int = Query(default=30, ge=1, le=365),
    current_user=Depends(get_current_user),
):
    user_id = str(current_user["_id"])
    docs = await repo.list_moods(user_id=user_id, limit=limit)
    return [_to_response(d) for d in docs]


@router.get("/trends", response_model=MoodTrendsResponse)
async def mood_trends(
    days: int = Query(default=7, ge=2, le=90),
    current_user=Depends(get_current_user),
):
    user_id = str(current_user["_id"])
    docs = await repo.list_recent_points(user_id=user_id, days=days)

    points = [
        MoodTrendPoint(date=date.fromisoformat(d["date"]), mood_score=d["mood_score"])
        for d in reversed(docs)  # oldest -> newest
    ]

    if not points:
        return MoodTrendsResponse(points=[], avg_7d=None)

    avg = round(sum(p.mood_score for p in points) / len(points), 2)
    return MoodTrendsResponse(points=points, avg_7d=avg)