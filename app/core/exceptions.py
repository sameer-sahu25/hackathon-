from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime, UTC
from typing import Any


class AppException(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Any = None
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


class RateLimitExceeded(AppException):
    def __init__(self, message: str = "Too many requests"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            code="RATE_LIMIT_EXCEEDED",
            message=message
        )


def create_success_response(data: Any, message: str = "Success") -> dict:
    return {
        "success": True,
        "data": data,
        "message": message,
        "timestamp": datetime.now(UTC).isoformat()
    }


def create_error_response(
    code: str,
    message: str,
    details: Any = None
) -> dict:
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details
        },
        "timestamp": datetime.now(UTC).isoformat()
    }


async def app_exception_handler(request: Request, exc: Exception):
    # Type ignore because FastAPI expects specific exception types, but Pylance is strict
    assert isinstance(exc, AppException)
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(exc.code, exc.message, exc.details)
    )


async def validation_exception_handler(request: Request, exc: Exception):
    assert isinstance(exc, RequestValidationError)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_response(
            "VALIDATION_ERROR",
            "Invalid request data",
            exc.errors()
        )
    )


async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            "INTERNAL_ERROR",
            "An unexpected error occurred"
        )
    )
