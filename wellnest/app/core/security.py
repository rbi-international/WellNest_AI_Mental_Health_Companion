from __future__ import annotations

from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext
from app.core.config import get_settings

pwd_context = CryptContext(
    schemes=["bcrypt_sha256", "bcrypt"],  # accept both (migration-friendly)
    deprecated="auto",
)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_access_token(data: dict, expires_minutes: int | None = None) -> str:
    settings = get_settings()
    to_encode = data.copy()

    exp_minutes = expires_minutes if expires_minutes is not None else settings.access_token_exp_minutes
    expire = datetime.now(timezone.utc) + timedelta(minutes=exp_minutes)
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])