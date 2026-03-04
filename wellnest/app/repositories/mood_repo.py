from __future__ import annotations

from datetime import datetime, timezone, date
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING

from app.db.mongodb import mongodb


class MoodRepository:
    async def ensure_indexes(self) -> None:
        # One mood log per user per day
        await mongodb.db.mood_logs.create_index(
            [("user_id", ASCENDING), ("date", ASCENDING)],
            unique=True,
            name="uniq_user_date",
        )
        # Efficient history/trend queries
        await mongodb.db.mood_logs.create_index(
            [("user_id", ASCENDING), ("date", DESCENDING)],
            name="idx_user_date_desc",
        )

    async def upsert_daily_mood(self, user_id: str, day: date, mood_score: int, notes: str | None):
        now = datetime.now(timezone.utc)

        result = await mongodb.db.mood_logs.find_one_and_update(
            {"user_id": user_id, "date": day.isoformat()},
            {
                "$set": {
                    "mood_score": mood_score,
                    "notes": notes,
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "user_id": user_id,
                    "date": day.isoformat(),
                    "created_at": now,
                },
            },
            upsert=True,
            return_document=True,
        )

        # Motor sometimes returns None depending on server config; fall back:
        if not result:
            result = await mongodb.db.mood_logs.find_one({"user_id": user_id, "date": day.isoformat()})

        return result

    async def list_moods(self, user_id: str, limit: int = 30):
        cursor = mongodb.db.mood_logs.find({"user_id": user_id}).sort("date", -1).limit(limit)
        return await cursor.to_list(length=limit)

    async def list_recent_points(self, user_id: str, days: int = 7):
        cursor = (
            mongodb.db.mood_logs.find({"user_id": user_id})
            .sort("date", -1)
            .limit(days)
        )
        return await cursor.to_list(length=days)

    async def delete_mood(self, user_id: str, day: date) -> int:
        res = await mongodb.db.mood_logs.delete_one({"user_id": user_id, "date": day.isoformat()})
        return res.deleted_count