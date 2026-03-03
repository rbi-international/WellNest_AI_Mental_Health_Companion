from fastapi import FastAPI
from app.core.config import get_settings
from app.core.logger import configure_logging, get_logger


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging()
    logger = get_logger("api")

    app = FastAPI(title=settings.app_name)

    @app.get("/health")
    async def health_check():
        return {
            "status": "ok",
            "environment": settings.environment
        }

    logger.info("application_started", environment=settings.environment)

    return app


app = create_app()