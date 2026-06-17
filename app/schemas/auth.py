from pydantic import BaseModel, EmailStr, field_validator  # type: ignore[reportMissingImports]
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.models.user import Language


class TokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None
    expires_in: int


class UserBase(BaseModel):
    language: Language = Language.EN


class UserCreateAnonymous(UserBase):
    pass


class UserCreateRegistered(UserBase):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID
    is_anonymous: bool
    email: Optional[EmailStr] = None
    language: Language
    created_at: datetime
    last_active_at: datetime

    class Config:
        from_attributes = True
