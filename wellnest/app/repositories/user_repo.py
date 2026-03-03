from __future__ import annotations

from datetime import datetime, timezone
from bson import ObjectId
from app.db.mongodb import mongodb


class UserRepository:
    async def get_by_email(self, email: str):
        return await mongodb.db.users.find_one({"email": email})

    async def get_by_id(self, user_id: str):
        return await mongodb.db.users.find_one({"_id": ObjectId(user_id)})

    async def create_user(self, email: str, password_hash: str, role: str = "user"):
        doc = {
            "email": email,
            "password_hash": password_hash,
            "role": role,
            "created_at": datetime.now(timezone.utc),
        }
        result = await mongodb.db.users.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc