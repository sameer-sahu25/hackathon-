import redis.asyncio as redis
from typing import Optional
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    _client: Optional[redis.Redis] = None

    @classmethod
    async def get_client(cls) -> redis.Redis:
        if cls._client is None:
            try:
                cls._client = redis.from_url(
                    settings.REDIS_URL,
                    max_connections=20,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    health_check_interval=30,
                    retry_on_timeout=True,
                    encoding="utf-8",
                    decode_responses=True
                )
                # Test connection
                await cls._client.ping()
                logger.info("Redis client connected successfully")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e} - cache will be bypassed")
        return cls._client

    @classmethod
    async def close(cls) -> None:
        if cls._client is not None:
            await cls._client.close()
            cls._client = None
            logger.info("Redis client closed")


async def get_redis_client() -> Optional[redis.Redis]:
    try:
        return await RedisClient.get_client()
    except Exception as e:
        logger.warning(f"Failed to get Redis client: {e}")
        return None
