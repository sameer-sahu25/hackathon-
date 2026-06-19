import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog
import sentry_sdk
from app.monitoring.middleware.pii_scrubber import scrub_dict

# Configure structlog
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip health, docs, openapi
        if request.url.path in ["/health", "/docs", "/openapi.json", "/redoc"]:
            return await call_next(request)

        start_time = time.time()
        request_id = str(uuid.uuid4())

        # Attach request_id to Sentry
        with sentry_sdk.configure_scope() as scope:
            scope.set_tag("request_id", request_id)

        # Get user info (placeholder, adjust to your auth system)
        user_id = None
        is_anonymous = True
        if hasattr(request.state, "user"):
            user_id = getattr(request.state.user, "id", None)
            is_anonymous = getattr(request.state.user, "is_anonymous", True)

        try:
            response: Response = await call_next(request)
            latency_ms = (time.time() - start_time) * 1000

            # Determine log level
            if response.status_code >= 500:
                log_level = logger.error
            elif response.status_code >=400:
                log_level = logger.warning
            else:
                log_level = logger.info

            log_level(
                "request_processed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                latency_ms=round(latency_ms,2),
                user_id=str(user_id) if user_id else None,
                is_anonymous=is_anonymous
            )
            response.headers["X-Request-ID"] = request_id
            return response

        except Exception as e:
            latency_ms = (time.time() - start_time) *1000
            logger.error(
                "request_failed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                latency_ms=round(latency_ms,2),
                user_id=str(user_id) if user_id else None,
                is_anonymous=is_anonymous,
                error=str(e)
            )
            raise
