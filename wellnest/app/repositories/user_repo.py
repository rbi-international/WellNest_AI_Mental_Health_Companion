from app.db.mongodb import mongodb
from bson import ObjectId
from datetime import datetime, timezone


class UserRepository:

    async def get_by_email(self, email: str):
        return await mongodb.db.users.find_one({"email": email})

    async def create_user(self, email: str, password_hash: str):
        user_data = {
            "email": email,
            "password_hash": password_hash,
            "created_at": datetime.now(timezone.utc)
        }

        result = await mongodb.db.users.insert_one(user_data)
        user_data["_id"] = result.inserted_id
        return user_data