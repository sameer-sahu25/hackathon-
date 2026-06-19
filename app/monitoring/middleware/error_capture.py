from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import sentry_sdk


class ErrorCaptureMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except HTTPException as e:
            # For HTTP exceptions, capture with context
            with sentry_sdk.push_scope() as scope:
                scope.set_tag("http.status_code", e.status_code)
                if e.status_code >=500:
                    sentry_sdk.capture_exception(e)
            raise
        except Exception as e:
            sentry_sdk.capture_exception(e)
            raise
