from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from src.enums.role import UserRole


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.CLIENT


class AdminUserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: UserRole


class UserUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    role: UserRole | None = None


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    role: UserRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)