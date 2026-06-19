from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4
from datetime import datetime, timezone

from app.auth.dependencies import (
    get_db,
    get_current_user,
    get_current_user_optional,
    require_registered_user
)
from app.auth.jwt_handler import JWTHandler
from app.auth.password_handler import PasswordHandler
from app.auth.token_blacklist import TokenBlacklist
from app.auth.exceptions import (
    InvalidCredentialsException,
    EmailAlreadyRegisteredException,
    PasswordTooWeakException,
    AccountDeactivatedException
)
from app.auth.rate_limiter import limiter
from app.db.models.user import User, Language
from app.schemas.auth import (
    AnonymousSessionRequest,
    AnonymousSessionResponse,
    RegisterRequest,
    RefreshRequest,
    LogoutRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UpgradeAnonymousRequest,
    UserResponse,
    TokenResponse,
    LogoutResponse,
    LogoutAllResponse,
    SuccessResponse
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# --- Anonymous Session ---
@router.post("/anonymous", response_model=AnonymousSessionResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/hour")
async def create_anonymous_session(
    request: Request,
    data: AnonymousSessionRequest,
    db: AsyncSession = Depends(get_db)
):
    session_id = str(uuid4())
    user = User(
        id=uuid4(),
        session_token=session_id,
        is_anonymous=True,
        language=data.preferred_language
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token, expires_in = JWTHandler.create_anonymous_token(
        session_id=str(user.id),
        language=user.language
    )

    return AnonymousSessionResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=expires_in,
        is_anonymous=True,
        session_id=str(user.id)
    )


# --- Register ---
@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
async def register_user(
    request: Request,
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    # Check email already exists
    result = await db.execute(select(User).where(User.email == data.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise EmailAlreadyRegisteredException()

    # Check password strength
    password_check = PasswordHandler.check_password_strength(data.password, data.email)
    if not password_check["is_strong"]:
        raise PasswordTooWeakException(feedback=password_check["feedback"])

    # Handle anonymous upgrade if token provided
    user = None
    if data.anonymous_token:
        try:
            anon_payload = await JWTHandler.decode_token(data.anonymous_token)
            if anon_payload.is_anonymous:
                result = await db.execute(select(User).where(User.id == anon_payload.sub))
                user = result.scalar_one_or_none()
                if user and user.is_anonymous:
                    # Blacklist anonymous token
                    await TokenBlacklist.blacklist_token(
                        anon_payload.jti,
                        anon_payload.exp - anon_payload.iat
                    )
        except Exception:
            pass

    if user:
        # Upgrade existing anonymous user
        user.is_anonymous = False
        user.email = data.email
        user.hashed_password = PasswordHandler.hash_password(data.password)
        user.language = Language(data.language)
    else:
        # Create new user
        user = User(
            id=uuid4(),
            session_token=str(uuid4()),
            is_anonymous=False,
            email=data.email,
            hashed_password=PasswordHandler.hash_password(data.password),
            language=Language(data.language)
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)

    # Create tokens
    access_token, access_expires = JWTHandler.create_access_token(
        user_id=str(user.id),
        is_anonymous=False,
        language=user.language
    )
    refresh_token, _ = JWTHandler.create_refresh_token(user_id=str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=access_expires,
        user=UserResponse.model_validate(user)
    )


# --- Login ---
@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/15minutes")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    # Find user by email (username in OAuth2 form is email)
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    if not user or not user.hashed_password:
        raise InvalidCredentialsException()

    # Verify password
    if not PasswordHandler.verify_password(form_data.password, user.hashed_password):
        raise InvalidCredentialsException()

    # Check account active
    if not user.is_active:
        raise AccountDeactivatedException()

    # Create tokens
    access_token, access_expires = JWTHandler.create_access_token(
        user_id=str(user.id),
        is_anonymous=False,
        language=user.language
    )
    refresh_token, _ = JWTHandler.create_refresh_token(user_id=str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=access_expires,
        user=UserResponse.model_validate(user)
    )


# --- Refresh Token ---
@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("10/hour")
async def refresh_token(
    request: Request,
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    # Verify refresh token
    payload = await JWTHandler.verify_refresh_token(data.refresh_token)

    # Blacklist old refresh token
    await TokenBlacklist.blacklist_token(
        payload.jti,
        payload.exp - payload.iat
    )

    # Get user
    result = await db.execute(select(User).where(User.id == payload.sub))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise InvalidCredentialsException()

    # Create new tokens
    access_token, access_expires = JWTHandler.create_access_token(
        user_id=str(user.id),
        is_anonymous=user.is_anonymous,
        language=user.language
    )
    new_refresh_token, _ = JWTHandler.create_refresh_token(user_id=str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=access_expires
    )


# --- Logout ---
@router.post("/logout", response_model=LogoutResponse)
async def logout(
    data: LogoutRequest,
    current_user: User = Depends(get_current_user)
):
    # Get the current access token from the dependency (we'll need to extract it differently)
    # For now, let's just blacklist the refresh token if provided
    if data.refresh_token:
        refresh_jti = JWTHandler.get_jti(data.refresh_token)
        if refresh_jti:
            await TokenBlacklist.blacklist_token(refresh_jti, 604800)  # 7 days

    return LogoutResponse(
        message="Successfully logged out",
        logged_out_at=datetime.now(timezone.utc)
    )


# --- Logout All ---
@router.post("/logout-all", response_model=LogoutAllResponse)
async def logout_all(
    current_password: str,
    current_user: User = Depends(require_registered_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify current password
    if not current_user.hashed_password or not PasswordHandler.verify_password(
        current_password,
        current_user.hashed_password
    ):
        raise InvalidCredentialsException()

    # Blacklist all tokens for user
    await TokenBlacklist.blacklist_all_user_tokens(str(current_user.id))

    return LogoutAllResponse(
        message="All sessions terminated",
        sessions_terminated_at=datetime.now(timezone.utc)
    )


# --- Get Current User ---
@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user)


# --- Change Password ---
@router.put("/change-password", response_model=TokenResponse)
async def change_password(
    data: ChangePasswordRequest,
    current_user: User = Depends(require_registered_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify current password
    if not current_user.hashed_password or not PasswordHandler.verify_password(
        data.current_password,
        current_user.hashed_password
    ):
        raise InvalidCredentialsException()

    # Check new password strength
    password_check = PasswordHandler.check_password_strength(
        data.new_password,
        current_user.email or ""
    )
    if not password_check["is_strong"]:
        raise PasswordTooWeakException(feedback=password_check["feedback"])

    # Update password
    current_user.hashed_password = PasswordHandler.hash_password(data.new_password)
    await db.commit()

    # Blacklist other sessions if requested
    if data.logout_other_sessions:
        await TokenBlacklist.blacklist_all_user_tokens(str(current_user.id))

    # Create new tokens
    access_token, access_expires = JWTHandler.create_access_token(
        user_id=str(current_user.id),
        is_anonymous=False,
        language=current_user.language
    )
    refresh_token, _ = JWTHandler.create_refresh_token(user_id=str(current_user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=access_expires
    )


# --- Forgot Password ---
@router.post("/forgot-password", response_model=SuccessResponse)
@limiter.limit("3/hour")
async def forgot_password(
    request: Request,
    data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    # Find user (always return same response)
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    # TODO: In real app, send email with reset token
    if user:
        reset_token, _ = JWTHandler.create_password_reset_token(str(user.id))
        # For demo purposes, log the token (never do this in production!)
        print(f"Password reset token for {user.email}: {reset_token}")

    return SuccessResponse(
        message="If that email is registered, you will receive reset instructions"
    )


# --- Reset Password ---
@router.post("/reset-password", response_model=TokenResponse)
async def reset_password(
    data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    # Verify reset token
    payload = await JWTHandler.decode_token(data.reset_token)
    if payload.type != "reset":
        raise InvalidCredentialsException()

    # Get user
    result = await db.execute(select(User).where(User.id == payload.sub))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise InvalidCredentialsException()

    # Check password strength
    password_check = PasswordHandler.check_password_strength(data.new_password, user.email or "")
    if not password_check["is_strong"]:
        raise PasswordTooWeakException(feedback=password_check["feedback"])

    # Update password
    user.hashed_password = PasswordHandler.hash_password(data.new_password)
    await db.commit()

    # Blacklist all tokens for user
    await TokenBlacklist.blacklist_all_user_tokens(str(user.id))

    # Blacklist reset token
    await TokenBlacklist.blacklist_token(payload.jti, 900)  # 15 mins

    # Create new tokens
    access_token, access_expires = JWTHandler.create_access_token(
        user_id=str(user.id),
        is_anonymous=False,
        language=user.language
    )
    refresh_token, _ = JWTHandler.create_refresh_token(user_id=str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=access_expires
    )


# --- Upgrade Anonymous to Registered ---
@router.post("/upgrade-anonymous", response_model=TokenResponse)
async def upgrade_anonymous(
    data: UpgradeAnonymousRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Must be anonymous
    if not current_user.is_anonymous:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already registered")

    # Check email not taken
    result = await db.execute(select(User).where(User.email == data.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise EmailAlreadyRegisteredException()

    # Check password strength
    password_check = PasswordHandler.check_password_strength(data.password, data.email)
    if not password_check["is_strong"]:
        raise PasswordTooWeakException(feedback=password_check["feedback"])

    # Upgrade user
    current_user.is_anonymous = False
    current_user.email = data.email
    current_user.hashed_password = PasswordHandler.hash_password(data.password)
    await db.commit()
    await db.refresh(current_user)

    # Create new tokens
    access_token, access_expires = JWTHandler.create_access_token(
        user_id=str(current_user.id),
        is_anonymous=False,
        language=current_user.language
    )
    refresh_token, _ = JWTHandler.create_refresh_token(user_id=str(current_user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=access_expires,
        user=UserResponse.model_validate(current_user)
    )
