import hashlib
import json
import logging
import redis.asyncio as redis
from typing import Any, Optional, List
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Multi-layer caching service for AI Core operations"""
    
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.ttl_rag = getattr(settings, 'CACHE_TTL_RAG', 21600)  # 6 hours
        self.ttl_rights = getattr(settings, 'CACHE_TTL_RIGHTS', 86400)  # 24 hours
        self.ttl_plans = getattr(settings, 'CACHE_TTL_PLANS', 3600)  # 1 hour
        self.ttl_embeddings = getattr(settings, 'CACHE_TTL_EMBEDDINGS', 604800)  # 7 days

    def _generate_md5(self, text: str) -> str:
        """Generate MD5 hash for cache keys"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    # LAYER 1: RAG Chunks Cache
    async def get_rag_chunks(self, state: str, situation_type: str, county: str) -> Optional[List[dict]]:
        """Get cached RAG chunks"""
        key = f"rag:{state}:{situation_type}:{self._generate_md5(county)}"
        cached = await self.redis.get(key)
        if cached:
            logger.info(f"Cache hit: RAG chunks for {state}")
            return json.loads(cached)
        return None

    async def set_rag_chunks(self, state: str, situation_type: str, county: str, chunks: List[dict]) -> None:
        """Cache RAG chunks"""
        key = f"rag:{state}:{situation_type}:{self._generate_md5(county)}"
        await self.redis.setex(key, self.ttl_rag, json.dumps(chunks))
        logger.info(f"Cache set: RAG chunks for {state}")

    # LAYER 2: State Rights Cards Cache
    async def get_rights_summary(self, state: str, language: str) -> Optional[dict]:
        """Get cached rights summary"""
        key = f"rights:{state}:{language}"
        cached = await self.redis.get(key)
        if cached:
            logger.info(f"Cache hit: Rights summary for {state} {language}")
            return json.loads(cached)
        return None

    async def set_rights_summary(self, state: str, language: str, summary: dict) -> None:
        """Cache rights summary"""
        key = f"rights:{state}:{language}"
        await self.redis.setex(key, self.ttl_rights, json.dumps(summary))
        logger.info(f"Cache set: Rights summary for {state} {language}")

    # LAYER 3: Action Plans Cache
    async def get_action_plan(self, state: str, situation: str, income: int, days: int) -> Optional[dict]:
        """Get cached action plan"""
        key = f"plan:{self._generate_md5(f'{state}{situation}{income}{days}')}"
        cached = await self.redis.get(key)
        if cached:
            logger.info("Cache hit: Action plan")
            return json.loads(cached)
        return None

    async def set_action_plan(self, state: str, situation: str, income: int, days: int, plan: dict) -> None:
        """Cache action plan"""
        key = f"plan:{self._generate_md5(f'{state}{situation}{income}{days}')}"
        await self.redis.setex(key, self.ttl_plans, json.dumps(plan))
        logger.info("Cache set: Action plan")

    # LAYER 4: Embeddings Cache
    async def get_embedding(self, query_text: str) -> Optional[List[float]]:
        """Get cached embedding"""
        key = f"embed:{self._generate_md5(query_text)}"
        cached = await self.redis.get(key)
        if cached:
            logger.info("Cache hit: Embedding")
            return json.loads(cached)
        return None

    async def set_embedding(self, query_text: str, embedding: List[float]) -> None:
        """Cache embedding"""
        key = f"embed:{self._generate_md5(query_text)}"
        await self.redis.setex(key, self.ttl_embeddings, json.dumps(embedding))
        logger.info("Cache set: Embedding")

    # Cache Invalidation
    async def flush_state_keys(self, state: str) -> None:
        """Flush all keys for a specific state"""
        pattern = f"rag:{state}:*"
        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)
        pattern = f"rights:{state}:*"
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            await self.redis.delete(*keys)
            logger.info(f"Flushed {len(keys)} keys for state {state}")

    async def flush_all_rag(self) -> None:
        """Flush all RAG and rights keys"""
        pattern = "rag:*"
        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)
        pattern = "rights:*"
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            await self.redis.delete(*keys)
            logger.info(f"Flushed {len(keys)} RAG and rights keys")

    async def flush_all(self) -> None:
        """Flush all cache keys"""
        await self.redis.flushdb()
        logger.info("Flushed all cache keys")
