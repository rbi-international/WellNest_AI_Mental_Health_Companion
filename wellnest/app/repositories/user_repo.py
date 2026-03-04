from app.db.mongodb import mongodb
from app.core.logger import get_logger

logger = get_logger("user_repository")


class UserRepository:

    async def get_by_email(self, email: str):
        logger.info("user_lookup_started", email=email)

        user = await mongodb.db.users.find_one({"email": email})

        if user:
            logger.info("user_lookup_success", email=email)
        else:
            logger.warning("user_lookup_not_found", email=email)

        return user

    async def create_user(self, email: str, password_hash: str, role: str = "user"):
        logger.info("user_creation_started", email=email)

        user = {
            "email": email,
            "password_hash": password_hash,
            "role": role
        }

        result = await mongodb.db.users.insert_one(user)

        logger.info("user_created", user_id=str(result.inserted_id))

        return result