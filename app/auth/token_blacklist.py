import time
from typing import Optional
from app.db.cache.redis_client import get_redis_client


class TokenBlacklist:
    @staticmethod
    async def blacklist_token(jti: str, expires_in: int) -> None:
        """Blacklist a single token by JTI"""
        redis = await get_redis_client()
        if redis:
            key = f"blacklist:jti:{jti}"
            await redis.setex(key, expires_in, "1")

    @staticmethod
    async def is_blacklisted(jti: str) -> bool:
        """Check if a token is blacklisted"""
        redis = await get_redis_client()
        if not redis:
            return False
        key = f"blacklist:jti:{jti}"
        return await redis.exists(key) > 0

    @staticmethod
    async def blacklist_all_user_tokens(user_id: str) -> None:
        """Blacklist all tokens for a user (stored timestamp)"""
        redis = await get_redis_client()
        if redis:
            key = f"blacklist:user:{user_id}"
            await redis.setex(key, 604800, str(int(time.time())))  # 7 days

    @staticmethod
    async def is_user_globally_blacklisted(user_id: str, token_iat: int) -> bool:
        """Check if token was issued before user's global blacklist time"""
        redis = await get_redis_client()
        if not redis:
            return False
        key = f"blacklist:user:{user_id}"
        ts_str = await redis.get(key)
        if not ts_str:
            return False
        try:
            ts = int(ts_str)
            return token_iat < ts
        except ValueError:
            return False
