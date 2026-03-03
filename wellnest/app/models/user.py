from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserInDB(BaseModel):
    id: str
    email: EmailStr
    password_hash: str
    created_at: datetime


class UserResponse(BaseModel):
    id: str
    email: EmailStr