from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger("mongodb")


class MongoDB:
    def __init__(self) -> None:
        self._client: AsyncIOMotorClient | None = None
        self._database: AsyncIOMotorDatabase | None = None

    async def connect(self) -> None:
        settings = get_settings()

        logger.info("attempting_mongodb_connection", uri=settings.mongo_uri, db=settings.mongo_db)

        try:
            self._client = AsyncIOMotorClient(settings.mongo_uri)

            # Connectivity check
            await self._client.admin.command("ping")

            # Explicit DB selection
            self._database = self._client[settings.mongo_db]

            # DB-level uniqueness: users.email
            await self._database.users.create_index("email", unique=True)

            logger.info("mongodb_connection_successful", db_name=self._database.name)

        except Exception as e:
            logger.error("mongodb_connection_failed", error=str(e))

            if self._client:
                self._client.close()

            self._client = None
            self._database = None
            raise RuntimeError("MongoDB connection failed") from e

    async def close(self) -> None:
        if self._client:
            logger.info("closing_mongodb_connection")
            self._client.close()

        self._client = None
        self._database = None

    @property
    def db(self) -> AsyncIOMotorDatabase:
        if self._database is None:
            raise RuntimeError("Database not initialized")
        return self._database


mongodb = MongoDB()