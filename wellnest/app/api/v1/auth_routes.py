from fastapi import APIRouter, HTTPException

from app.models.user import UserLogin, UserCreate
from app.repositories.user_repo import UserRepository
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token
)
from app.core.logger import get_logger

router = APIRouter(prefix="/auth", tags=["Auth"])

logger = get_logger("auth")
user_repo = UserRepository()


@router.post("/register")
async def register(user: UserCreate):

    email = user.email.strip().lower()

    logger.info("auth_register_attempt", email=email)

    existing = await user_repo.get_by_email(email)

    if existing:
        logger.warning("auth_register_duplicate", email=email)
        raise HTTPException(status_code=409, detail="Email already registered")

    password_hash = hash_password(user.password)

    await user_repo.create_user(email, password_hash)

    logger.info("auth_register_success", email=email)

    return {"message": "User registered successfully"}


@router.post("/login")
async def login(user: UserLogin):

    email = user.email.strip().lower()

    logger.info("auth_login_attempt", email=email)

    db_user = await user_repo.get_by_email(email)

    if not db_user:
        logger.warning("auth_user_not_found", email=email)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(user.password, db_user["password_hash"]):
        logger.warning("auth_password_invalid", email=email)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    logger.info("auth_password_verified", user_id=str(db_user["_id"]))

    token = create_access_token(
        {
            "sub": str(db_user["_id"]),
            "role": db_user.get("role", "user")
        }
    )

    logger.info("auth_login_success", user_id=str(db_user["_id"]))

    return {
        "access_token": token,
        "token_type": "bearer"
    }