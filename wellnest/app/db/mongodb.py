from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger("mongodb")


class MongoDB:
    def __init__(self):
        self._client: AsyncIOMotorClient | None = None
        self._database = None

    async def connect(self):
        settings = get_settings()
        logger.info("attempting_mongodb_connection")

        try:
            self._client = AsyncIOMotorClient(settings.mongo_uri)
            await self._client.admin.command("ping")

            # Explicit DB name (more reliable than get_default_database)
            self._database = self._client.get_database()

            logger.info("mongodb_connection_successful")

        except Exception as e:
            logger.error(f"mongodb_connection_failed: {e}")
            raise RuntimeError("MongoDB connection failed")

    async def close(self):
        if self._client:
            logger.info("closing_mongodb_connection")
            self._client.close()

    @property
    def db(self):
        if not self._database:
            raise RuntimeError("Database not initialized")
        return self._database


mongodb = MongoDB()