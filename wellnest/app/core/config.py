from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = Field(default="WellNest")
    environment: str = Field(default="development")

    mongo_uri: str
    jwt_secret: str

    ai_provider: str = Field(default="openai")
    ai_model: str = Field(default="gpt-4o-mini")

    model_config = {
        "env_file": ".env",
        "case_sensitive": False
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()