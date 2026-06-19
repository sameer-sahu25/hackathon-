from pydantic import BaseModel, EmailStr
from typing import Optional, Literal
from uuid import UUID
from datetime import datetime
from app.db.models.user import Language


# Request schemas
class AnonymousSessionRequest(BaseModel):
    preferred_language: Literal["EN", "ES"] = "EN"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    language: Literal["EN", "ES"] = "EN"
    anonymous_token: Optional[str] = None


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    logout_other_sessions: bool = True


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    reset_token: str
    new_password: str


class UpgradeAnonymousRequest(BaseModel):
    email: EmailStr
    password: str


# Response schemas
class UserResponse(BaseModel):
    id: UUID
    email: Optional[EmailStr] = None
    is_anonymous: bool
    language: str
    state: Optional[str] = None
    created_at: datetime
    last_active_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnonymousSessionResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    is_anonymous: bool = True
    session_id: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int
    user: Optional[UserResponse] = None


class SuccessResponse(BaseModel):
    message: str


class LogoutResponse(SuccessResponse):
    logged_out_at: datetime


class LogoutAllResponse(SuccessResponse):
    sessions_terminated_at: datetime

