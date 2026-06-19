import functools
import hashlib
import logging
from typing import Any, Callable, Optional, Type, List
from pydantic import BaseModel
from app.db.cache.cache_service import CacheService
from app.db.cache.cache_keys import CacheKeys, RATE_LIMIT_TTL
from app.core.exceptions import RateLimitExceeded

logger = logging.getLogger(__name__)


def cache_result(key_template: str, ttl: int):
    """Decorator to cache async function results"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from args and kwargs
            key_parts = [key_template]
            if args:
                key_parts.append(str(args))
            if kwargs:
                key_parts.append(str(sorted(kwargs.items())))
            
            key = CacheKeys.make_key(*key_parts)
            
            # Try to get from cache
            cached = await CacheService.get(key)
            if cached is not None:
                return cached
            
            # Call function and cache result
            result = await func(*args, **kwargs)
            await CacheService.set(key, result, ttl)
            return result
        return wrapper
    return decorator


def invalidate_cache(patterns: List[str]):
    """Decorator to invalidate cache after write operations"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            for pattern in patterns:
                try:
                    await CacheService.delete_pattern(pattern)
                except Exception as e:
                    logger.warning(f"Failed to invalidate pattern {pattern}: {e}")
                    
            return result
        return wrapper
    return decorator


def rate_limit(limit: int, window: int, key_prefix: str):
    """Redis-based rate limiting decorator"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract key from kwargs or args
            identifier = kwargs.get("user_id") or kwargs.get("ip") or "unknown"
            endpoint = key_prefix
            
            key = CacheKeys.make_key("ratelimit", endpoint, identifier)
            count = await CacheService.increment(key, window)
            
            if count > limit:
                logger.warning(f"Rate limit exceeded for {identifier} on {endpoint}")
                raise RateLimitExceeded()
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
