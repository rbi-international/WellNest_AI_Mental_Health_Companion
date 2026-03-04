from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt
from bson import ObjectId

from app.core.config import get_settings
from app.db.mongodb import mongodb
from app.core.logger import get_logger

settings = get_settings()
security = HTTPBearer()

logger = get_logger("auth_dependency")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )

        user_id = payload.get("sub")

        logger.info("jwt_payload_decoded", user_id=user_id)

        if not user_id:
            raise HTTPException(status_code=401)

        user = await mongodb.db.users.find_one(
            {"_id": ObjectId(user_id)}
        )

        if not user:
            logger.warning("jwt_user_not_found", user_id=user_id)
            raise HTTPException(status_code=401)

        return user

    except Exception as e:
        logger.error("jwt_verification_failed", error=str(e))
        raise HTTPException(status_code=401)