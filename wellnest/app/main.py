from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.v1.mood_routes import router as mood_router
from app.api.v1.auth_routes import router as auth_router
from app.core.config import get_settings
from app.core.logger import configure_logging, get_logger
from app.db.mongodb import mongodb
from app.repositories.mood_repo import MoodRepository


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging()
    logger = get_logger("api")

    logger.info("application_startup")

    await mongodb.connect()

    # Ensure mood indexes
    await MoodRepository().ensure_indexes()

    yield

    await mongodb.close()
    logger.info("application_shutdown")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        lifespan=lifespan
    )

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "environment": settings.environment}

    app.include_router(auth_router)
    app.include_router(mood_router)

    return app


app = create_app()