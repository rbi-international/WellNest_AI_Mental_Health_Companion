from fastapi import APIRouter, HTTPException, Depends
from app.models.user import UserCreate
from app.repositories.user_repo import UserRepository
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

user_repo = UserRepository()


@router.post("/register")
async def register(user: UserCreate):
    existing = await user_repo.get_by_email(user.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = hash_password(user.password)
    created_user = await user_repo.create_user(user.email, hashed)

    return {"message": "User registered successfully"}


@router.post("/login")
async def login(user: UserCreate):
    db_user = await user_repo.get_by_email(user.email)

    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(user.password, db_user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(db_user["_id"])})

    return {"access_token": token, "token_type": "bearer"}