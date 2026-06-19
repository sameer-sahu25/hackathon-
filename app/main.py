from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.config import settings
from app.api.v1.router import api_router
from app.core.exceptions import (
    AppException,
    app_exception_handler,
    validation_exception_handler,
    general_exception_handler
)
from app.auth.rate_limiter import limiter, rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
from app.monitoring.sentry_config import init_sentry
from app.monitoring.posthog_config import init_posthog
from app.monitoring.middleware.request_logging import RequestLoggingMiddleware
from app.monitoring.middleware.error_capture import ErrorCaptureMiddleware
from app.monitoring.dashboards.impact_dashboard import ImpactDashboardService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_sentry()
    init_posthog()
    yield
    # Shutdown


app = FastAPI(
    title=settings.APP_NAME,
    description="Production-grade backend for Housing Stability AI Guide - helping renters facing eviction",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Rate Limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Monitoring middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(ErrorCaptureMiddleware)

# Security Headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    if settings.APP_ENV != "development":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# Exception Handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include API Router
app.include_router(api_router)


@app.get("/")
async def root():
    return {"message": "Welcome to the Housing Stability AI Guide API", "docs": "/docs"}


@app.get("/health/detailed")
async def detailed_health():
    """Detailed health check with dependencies"""
    from app.db.session import async_engine
    from sqlalchemy import text

    db_ok = False
    try:
        async with async_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            db_ok = True
    except Exception:
        pass

    return {
        "status": "ok" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
        "version": "1.0.0"
    }


@app.get("/api/v1/analytics/impact", tags=["Analytics"])
async def get_impact_metrics():
    """Public impact dashboard endpoint for judges"""
    return await ImpactDashboardService.get_live_impact_metrics()


@app.get("/api/v1/analytics/trend", tags=["Analytics"])
async def get_daily_trend(days: int =7):
    """Daily trend for demo"""
    return await ImpactDashboardService.get_daily_trend(days=days)


@app.get("/api/v1/analytics/engineering", tags=["Analytics"])
async def get_engineering_health():
    """Engineering health dashboard"""
    return await ImpactDashboardService.get_engineering_health()
