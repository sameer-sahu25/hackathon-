from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    # App
    APP_ENV: Literal["development", "staging", "production"] = "development"
    APP_NAME: str = "Housing Stability AI"
    SECRET_KEY: str
    DEBUG: bool = True

    # Database
    DATABASE_URL: str
    DATABASE_URL_SYNC: str

    # Redis
    REDIS_URL: str

    # Anthropic
    ANTHROPIC_API_KEY: str
    CLAUDE_MODEL: str = "claude-sonnet-4-6"
    CLAUDE_MAX_TOKENS: int = 2000
    CLAUDE_TEMPERATURE: float = 0.3
    CLAUDE_MAX_RETRIES: int = 3

    # Pinecone
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str
    PINECONE_INDEX_NAME: str
    PINECONE_NAMESPACE_LAWS: str = "state-laws"
    PINECONE_NAMESPACE_PROGRAMS: str = "hud-programs"
    PINECONE_NAMESPACE_FORMS: str = "court-forms"

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_EMBEDDING_DIMENSIONS: int = 1536

    # Redis Cache
    CACHE_TTL_RAG: int = 21600  # 6 hours
    CACHE_TTL_RIGHTS: int = 86400  # 24 hours
    CACHE_TTL_PLANS: int = 3600  # 1 hour
    CACHE_TTL_EMBEDDINGS: int = 604800  # 7 days
    
    # Integration-specific Cache TTLs
    CACHE_TTL_GEOCODE: int = 2592000  # 30 days
    CACHE_TTL_PLACES: int = 1800  # 30 minutes
    CACHE_TTL_PLACE_DETAILS: int = 86400  # 24 hours
    CACHE_TTL_DISTANCE: int = 1800  # 30 minutes
    CACHE_TTL_HUD: int = 3600  # 1 hour
    CACHE_TTL_211: int = 3600  # 1 hour
    CACHE_TTL_DATAGOV: int = 86400  # 24 hours
    CACHE_TTL_PDF: int = 86400  # 24 hours

    # AI Safety
    AI_MIN_CONFIDENCE_SCORE: float = 0.70
    AI_SAFETY_STRICT_MODE: bool = True

    # Twilio
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str
    TWILIO_STATUS_CALLBACK_URL: str = ""

    # Google Maps
    GOOGLE_MAPS_API_KEY: str
    GOOGLE_MAPS_DAILY_QUOTA: int = 10000

    # HUD + 211
    HUD_API_KEY: str
    HUD_API_BASE_URL: str = "https://www.hud.gov"
    API_211_KEY: str
    API_211_BASE_URL: str = "https://api.211.org"
    
    # Data.gov
    DATA_GOV_API_KEY: str = ""
    DATA_GOV_API_BASE_URL: str = "https://catalog.data.gov/api/3"
    
    # NLIHC
    NLIHC_CSV_PATH: str = ""

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Monitoring
    SENTRY_DSN: str = ""
    SENTRY_ENVIRONMENT: str = "development"
    SENTRY_TRACES_SAMPLE_RATE: float = 0.2
    SENTRY_PROFILES_SAMPLE_RATE: float = 0.1
    POSTHOG_API_KEY: str = ""
    POSTHOG_HOST: str = "https://app.posthog.com"
    POSTHOG_DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    APP_VERSION: str = "1.0.0"

    # CORS
    FRONTEND_URL: str = "http://localhost:3000"

    # Celery
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()  # type: ignore
