from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_access_token(data: dict, expires_delta: int = 90):
    settings = get_settings()
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm="HS256"
    )


def decode_access_token(token: str):
    settings = get_settings()
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=["HS256"]
    )