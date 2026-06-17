from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.dependencies import get_db, get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    get_password_hash,
    generate_session_token
)
from app.models.user import User
from app.schemas.auth import (
    UserCreateAnonymous,
    UserCreateRegistered,
    UserLogin,
    UserResponse,
    TokenData
)
from app.core.exceptions import create_success_response
from datetime import timedelta
from uuid import uuid4
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/anonymous", response_model=dict)
async def create_anonymous_user(
    data: UserCreateAnonymous,
    db: AsyncSession = Depends(get_db)
):
    """Create an anonymous user session with JWT"""
    user = User(
        id=uuid4(),
        session_token=generate_session_token(),
        is_anonymous=True,
        language=data.language
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return create_success_response(
        TokenData(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=int(access_token_expires.total_seconds())
        ).model_dump(),
        "Anonymous session created successfully"
    )


@router.post("/register", response_model=dict)
async def register_user(
    data: UserCreateRegistered,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user with email/password"""
    result = await db.execute(select(User).where(User.email == data.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    user = User(
        id=uuid4(),
        session_token=generate_session_token(),
        is_anonymous=False,
        email=data.email,
        hashed_password=get_password_hash(data.password),
        language=data.language
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return create_success_response(
        {
            "user": UserResponse.model_validate(user).model_dump(),
            "token": TokenData(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=int(access_token_expires.total_seconds())
            ).model_dump()
        },
        "User registered successfully"
    )


@router.post("/login", response_model=dict)
async def login_user(
    data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Login with email/password"""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    if not user or not user.hashed_password or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(data={"sub": str(user.id)})

    return create_success_response(
        {
            "user": UserResponse.model_validate(user).model_dump(),
            "token": TokenData(
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=int(access_token_expires.total_seconds())
            ).model_dump()
        },
        "Login successful"
    )


@router.get("/me", response_model=dict)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return create_success_response(
        UserResponse.model_validate(current_user).model_dump(),
        "User retrieved successfully"
    )
