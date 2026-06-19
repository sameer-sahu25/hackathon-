import json
import logging
from typing import Optional, Any, Callable, Dict, List
from pydantic import BaseModel
from app.db.cache.redis_client import get_redis_client
from app.db.cache.cache_keys import CacheKeys

logger = logging.getLogger(__name__)


class CacheService:
    @staticmethod
    async def get(key: str) -> Optional[Any]:
        try:
            redis_client = await get_redis_client()
            if not redis_client:
                return None
            data = await redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.warning(f"Cache get failed for key {key}: {e}")
            return None

    @staticmethod
    async def set(key: str, value: Any, ttl: int) -> bool:
        try:
            redis_client = await get_redis_client()
            if not redis_client:
                return False
            if isinstance(value, (dict, list)):
                serialized = json.dumps(value)
            elif isinstance(value, BaseModel):
                serialized = value.model_dump_json()
            else:
                serialized = str(value)
            await redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.warning(f"Cache set failed for key {key}: {e}")
            return False

    @staticmethod
    async def delete(key: str) -> bool:
        try:
            redis_client = await get_redis_client()
            if not redis_client:
                return False
            await redis_client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete failed for key {key}: {e}")
            return False

    @staticmethod
    async def delete_pattern(pattern: str) -> int:
        try:
            redis_client = await get_redis_client()
            if not redis_client:
                return 0
            keys = await redis_client.keys(pattern)
            if keys:
                await redis_client.delete(*keys)
                return len(keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache delete pattern failed for {pattern}: {e}")
            return 0

    @staticmethod
    async def exists(key: str) -> bool:
        try:
            redis_client = await get_redis_client()
            if not redis_client:
                return False
            return await redis_client.exists(key) > 0
        except Exception as e:
            logger.warning(f"Cache exists check failed for key {key}: {e}")
            return False

    @staticmethod
    async def increment(key: str, ttl: int) -> int:
        try:
            redis_client = await get_redis_client()
            if not redis_client:
                return 0
            count = await redis_client.incr(key)
            if count == 1:
                await redis_client.expire(key, ttl)
            return count
        except Exception as e:
            logger.warning(f"Cache increment failed for key {key}: {e}")
            return 0

    @staticmethod
    async def get_or_set(key: str, fetch_fn: Callable, ttl: int) -> Any:
        try:
            cached = await CacheService.get(key)
            if cached is not None:
                return cached
            data = await fetch_fn()
            await CacheService.set(key, data, ttl)
            return data
        except Exception as e:
            logger.warning(f"Cache get_or_set failed for key {key}: {e}")
            return await fetch_fn()

    @staticmethod
    async def invalidate_state(state: str) -> None:
        try:
            patterns = [
                f"rag:{state}:*",
                f"plan:{state}:*",
                f"rights:{state}:*",
                f"checklist:{state}:*",
                f"resources:{state}:*",
            ]
            for pattern in patterns:
                await CacheService.delete_pattern(pattern)
        except Exception as e:
            logger.warning(f"State invalidation failed for {state}: {e}")

    @staticmethod
    async def warm_cache(states: List[str]) -> None:
        logger.info(f"Warming cache for states: {states}")
        try:
            for state in states:
                for lang in ["EN", "ES"]:
                    await CacheService.invalidate_state(state)
        except Exception as e:
            logger.warning(f"Cache warming failed: {e}")
