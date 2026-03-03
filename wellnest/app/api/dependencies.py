from __future__ import annotations

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import decode_access_token
from app.repositories.user_repo import UserRepository

security = HTTPBearer()
user_repo = UserRepository()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials

    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        user = await user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        return user

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def require_role(required_role: str):
    async def role_checker(current_user=Depends(get_current_user)):
        role = current_user.get("role", "user")
        if role != required_role:
            raise HTTPException(status_code=403, detail="Forbidden")
        return current_user

    return role_checker