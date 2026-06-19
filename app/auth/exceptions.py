from typing import Optional
from fastapi import HTTPException, status


class AuthException(HTTPException):
    """Base authentication exception"""
    pass


class InvalidCredentialsException(AuthException):
    """Raised when credentials are invalid"""
    def __init__(self, detail: str = "Invalid credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class TokenExpiredException(AuthException):
    """Raised when token has expired"""
    def __init__(self, detail: str = "Token has expired"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class TokenBlacklistedException(AuthException):
    """Raised when token is blacklisted"""
    def __init__(self, detail: str = "Token has been invalidated"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class InvalidTokenTypeException(AuthException):
    """Raised when token type is invalid"""
    def __init__(self, detail: str = "Invalid token type"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AccountDeactivatedException(AuthException):
    """Raised when user account is deactivated"""
    def __init__(self, detail: str = "Account has been deactivated"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
        )


class EmailAlreadyRegisteredException(AuthException):
    """Raised when email is already registered"""
    def __init__(self, detail: str = "Email already registered"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class PasswordTooWeakException(AuthException):
    """Raised when password is too weak"""
    def __init__(self, detail: str = "Password is too weak", feedback: Optional[list[str]] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )
        self.feedback = feedback or []


class UserNotFoundException(AuthException):
    """Raised when user not found"""
    def __init__(self, detail: str = "User not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class RequiresRegisteredUserRequiredException(AuthException):
    """Raised when endpoint requires registered user but anonymous provided"""
    def __init__(self, detail: str = "Registered user required"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class AdminUserRequiredException(AuthException):
    """Raised when endpoint requires admin user"""
    def __init__(self, detail: str = "Admin user required"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )
