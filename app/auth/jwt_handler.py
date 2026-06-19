from datetime import datetime, timedelta, timezone
from typing import Optional, Literal
from jose import JWTError, jwt  # type: ignore
from pydantic import BaseModel
import uuid
from app.config import settings
from app.auth.token_blacklist import TokenBlacklist
from app.auth.exceptions import (
    InvalidCredentialsException,
    TokenExpiredException,
    TokenBlacklistedException,
    InvalidTokenTypeException
)


class TokenPayload(BaseModel):
    sub: str
    type: Literal["access", "refresh", "reset"]
    is_anonymous: bool = False
    language: str = "EN"
    state: Optional[str] = None
    iat: int
    exp: int
    jti: str


class JWTHandler:
    @staticmethod
    def _generate_jti() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def create_access_token(
        user_id: str,
        is_anonymous: bool = False,
        language: str = "EN",
        state: Optional[str] = None
    ) -> tuple[str, int]:
        """Create an access token, returns (token, expires_in_seconds)"""
        expires_in = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        jti = JWTHandler._generate_jti()
        to_encode = {
            "sub": str(user_id),
            "type": "access",
            "is_anonymous": is_anonymous,
            "language": language,
            "state": state,
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
            "jti": jti
        }
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt, expires_in

    @staticmethod
    def create_refresh_token(user_id: str) -> tuple[str, int]:
        """Create a refresh token, returns (token, expires_in_seconds)"""
        expires_in = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        jti = JWTHandler._generate_jti()
        to_encode = {
            "sub": str(user_id),
            "type": "refresh",
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
            "jti": jti
        }
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt, expires_in

    @staticmethod
    def create_anonymous_token(
        session_id: str,
        language: str = "EN",
        state: Optional[str] = None
    ) -> tuple[str, int]:
        """Create an anonymous access token, returns (token, expires_in_seconds)"""
        expires_in = 24 * 60 * 60  # 24 hours
        now = datetime.now(timezone.utc)
        expire = now + timedelta(hours=24)
        jti = JWTHandler._generate_jti()
        to_encode = {
            "sub": str(session_id),
            "type": "access",
            "is_anonymous": True,
            "language": language,
            "state": state,
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
            "jti": jti
        }
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt, expires_in

    @staticmethod
    def create_password_reset_token(user_id: str) -> tuple[str, int]:
        """Create a password reset token, returns (token, expires_in_seconds)"""
        expires_in = 15 * 60  # 15 minutes
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=15)
        jti = JWTHandler._generate_jti()
        to_encode = {
            "sub": str(user_id),
            "type": "reset",
            "iat": int(now.timestamp()),
            "exp": int(expire.timestamp()),
            "jti": jti
        }
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt, expires_in

    @staticmethod
    async def decode_token(token: str) -> TokenPayload:
        """Decode and verify token, raises exceptions on failure"""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_exp": True}
            )
            token_payload = TokenPayload(**payload)
        except JWTError as e:
            # Check if expired
            try:
                payload = jwt.decode(
                    token,
                    settings.JWT_SECRET_KEY,
                    algorithms=[settings.JWT_ALGORITHM],
                    options={"verify_exp": False}
                )
                now = datetime.now(timezone.utc).timestamp()
                if payload.get("exp", 0) < now:
                    raise TokenExpiredException()
            except TokenExpiredException:
                raise
            raise InvalidCredentialsException()

        # Check blacklist
        if await TokenBlacklist.is_blacklisted(token_payload.jti):
            raise TokenBlacklistedException()

        # Check user global blacklist
        if await TokenBlacklist.is_user_globally_blacklisted(
            token_payload.sub,
            token_payload.iat
        ):
            raise TokenBlacklistedException()

        return token_payload

    @staticmethod
    async def verify_refresh_token(token: str) -> TokenPayload:
        """Verify refresh token, returns payload"""
        payload = await JWTHandler.decode_token(token)
        if payload.type != "refresh":
            raise InvalidTokenTypeException("Expected refresh token")
        return payload

    @staticmethod
    def get_jti(token: str) -> str:
        """Extract JTI without full verification"""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_signature": False, "verify_exp": False}
            )
            return payload.get("jti", "")
        except JWTError:
            return ""

    @staticmethod
    def is_token_expired(token: str) -> bool:
        """Check if token is expired without raising"""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_signature": False, "verify_exp": False}
            )
            now = datetime.now(timezone.utc).timestamp()
            return payload.get("exp", 0) < now
        except JWTError:
            return True
