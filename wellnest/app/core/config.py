from pathlib import Path
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parents[2]  # points to .../wellnest


class Settings(BaseSettings):
    # --------------------------------------------------
    # Application
    # --------------------------------------------------
    app_name: str = Field(default="WellNest")
    environment: str = Field(default="development")

    # --------------------------------------------------
    # MongoDB
    # --------------------------------------------------
    mongo_uri: str
    mongo_db: str = Field(default="wellnest")

    # --------------------------------------------------
    # Authentication / JWT
    # --------------------------------------------------
    jwt_secret: str
    jwt_algorithm: str = Field(default="HS256")
    access_token_exp_minutes: int = Field(default=60)

    # --------------------------------------------------
    # AI Provider
    # --------------------------------------------------
    ai_provider: str = Field(default="openai")
    ai_model: str = Field(default="gpt-4o-mini")

    # --------------------------------------------------
    # Environment Configuration
    # --------------------------------------------------
    model_config = {
        "env_file": str(BASE_DIR / ".env"),
        "case_sensitive": False,
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()