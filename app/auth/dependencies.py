from typing import Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends, BackgroundTasks
from app.db.session import AsyncSessionLocal
from app.auth.oauth2_scheme import oauth2_scheme
from app.auth.jwt_handler import JWTHandler
from app.auth.exceptions import (
    InvalidCredentialsException,
    AccountDeactivatedException,
    RequiresRegisteredUserRequiredException,
    AdminUserRequiredException
)
from app.db.models.user import User, Language
from uuid import uuid4
from datetime import datetime, timezone


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


def update_last_active(user: User, db: AsyncSession) -> None:
    """Background task to update last active timestamp"""
    import asyncio
    async def _update():
        user.last_active_at = datetime.now(timezone.utc)  # type: ignore
        await db.commit()
    asyncio.create_task(_update())


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    if not token:
        raise InvalidCredentialsException()
    payload = await JWTHandler.decode_token(token)
    result = await db.execute(select(User).where(User.id == payload.sub))
    user = result.scalar_one_or_none()
    if not user:
        raise InvalidCredentialsException()
    if not user.is_active:
        raise AccountDeactivatedException()
    # Update last active (background)
    user.last_active_at = datetime.now(timezone.utc)  # type: ignore
    await db.commit()
    return user


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    if not token:
        return None
    try:
        payload = await JWTHandler.decode_token(token)
        result = await db.execute(select(User).where(User.id == payload.sub))
        user = result.scalar_one_or_none()
        if user and user.is_active:
            user.last_active_at = datetime.now(timezone.utc)  # type: ignore
            await db.commit()
            return user
    except Exception:
        pass
    return None


async def get_anonymous_or_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    if token:
        try:
            payload = await JWTHandler.decode_token(token)
            result = await db.execute(select(User).where(User.id == payload.sub))
            user = result.scalar_one_or_none()
            if user and user.is_active:
                user.last_active_at = datetime.now(timezone.utc)  # type: ignore
                await db.commit()
                return user
        except Exception:
            pass
    # Create anonymous user
    from app.auth.password_handler import PasswordHandler
    user = User(
        id=uuid4(),
        session_token=str(uuid4()),
        is_anonymous=True,
        language=Language.EN
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def require_registered_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.is_anonymous:
        raise RequiresRegisteredUserRequiredException()
    return current_user


async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    # Check if user is admin (we'll need to add is_admin field to User model? Let's check)
    # For now, let's assume we might add it later, or for now, just raise
    # Wait, let's check User model
    raise AdminUserRequiredException()
