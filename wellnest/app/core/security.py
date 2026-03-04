from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.core.logger import get_logger

settings = get_settings()
logger = get_logger("security")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_access_token(data: dict) -> str:
    try:
        payload = data.copy()

        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_exp_minutes
        )

        payload.update({"exp": expire})

        token = jwt.encode(
            payload,
            settings.jwt_secret,
            algorithm=settings.jwt_algorithm,
        )

        logger.info("jwt_token_created", user_id=data.get("sub"))

        return token

    except Exception as e:
        logger.error("jwt_generation_failed", error=str(e))
        raise