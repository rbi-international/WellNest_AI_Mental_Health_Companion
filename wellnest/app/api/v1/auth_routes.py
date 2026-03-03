from __future__ import annotations

from fastapi import APIRouter, HTTPException, Depends
from pymongo.errors import DuplicateKeyError

from app.models.user import UserCreate
from app.repositories.user_repo import UserRepository
from app.core.security import hash_password, verify_password, create_access_token
from app.api.dependencies import get_current_user, require_role

router = APIRouter(prefix="/auth", tags=["auth"])

user_repo = UserRepository()


@router.post("/register")
async def register(user: UserCreate):
    email = user.email.strip().lower()

    # Application-level check (nice error)
    existing = await user_repo.get_by_email(email)
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    try:
        hashed = hash_password(user.password)
        await user_repo.create_user(email=email, password_hash=hashed, role="user")
        return {"message": "User registered successfully"}

    except DuplicateKeyError:
        # DB-level check (race condition safe)
        raise HTTPException(status_code=409, detail="Email already registered")


@router.post("/login")
async def login(user: UserCreate):
    email = user.email.strip().lower()

    db_user = await user_repo.get_by_email(email)
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(user.password, db_user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(
        {
            "sub": str(db_user["_id"]),
            "role": db_user.get("role", "user"),
        }
    )

    return {"access_token": token, "token_type": "bearer"}


@router.get("/me")
async def get_me(current_user=Depends(get_current_user)):
    return {
        "id": str(current_user["_id"]),
        "email": current_user["email"],
        "role": current_user.get("role", "user"),
        "created_at": current_user["created_at"],
    }


# Optional: quick role test (keep for now, remove later)
@router.get("/admin-only")
async def admin_only(_=Depends(require_role("admin"))):
    return {"message": "You are admin"}