import time
from typing import List, Dict, Optional
from app.integrations.hud.client import get_hud_client
from app.integrations.hud.mapper import normalize_hud_program
from app.integrations.shared.logger import IntegrationLogger
from app.integrations.shared.circuit_breaker import get_hud_circuit
from app.integrations.shared.fallbacks import get_fallback_resources
from app.config import settings
import redis.asyncio as redis
import sentry_sdk
from tenacity import retry, stop_after_attempt, wait_exponential

redis_client: Optional[redis.Redis] = None


async def get_redis_client():
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(settings.REDIS_URL)
    return redis_client


class HudService:
    def __init__(self):
        self.client = get_hud_client()

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
    async def search_programs(
        self,
        state: str,
        county: Optional[str] = None,
        income_monthly: Optional[int] = None,
        household_size: Optional[int] = None
    ) -> List[Dict]:
        start_time = time.time()
        cache_key = f"hud:{state}:{county or 'all'}"
        
        r = await get_redis_client()
        cached = await r.get(cache_key)
        if cached:
            IntegrationLogger.log_call(
                integration="hud",
                method="search_programs",
                latency_ms=(time.time() - start_time) * 1000,
                cache_hit=True,
                status="success"
            )
            return eval(cached.decode('utf-8'))
        
        try:
            async def _fetch_hud():
                # Mock response in case HUD API is not available (replace with real endpoint when known)
                # For demo purposes, we'll return a mock response or fallback
                response = await self.client.get("/program_offices/housing/programs/affordablehousing/", params={
                    "state": state,
                    "county": county
                })
                response.raise_for_status()
                data = response.json()
                return [normalize_hud_program(p) for p in data.get("programs", [])]
            
            circuit = get_hud_circuit()
            programs = await circuit(_fetch_hud)
            
            await r.setex(cache_key, settings.CACHE_TTL_HUD, str(programs))
            
            IntegrationLogger.log_call(
                integration="hud",
                method="search_programs",
                latency_ms=(time.time() - start_time) * 1000,
                cache_hit=False,
                status="success"
            )
            
            return programs
        except Exception as e:
            sentry_sdk.capture_exception(e)
            # Fallback: return HUD-like resources from our fallback data
            fallback = get_fallback_resources(state)
            return [
                {
                    "name": "Housing Assistance (Local)",
                    "description": "Local housing resources available - call 211 for details",
                    "state": state,
                    "county": county,
                    "eligibility": "Contact 211 for eligibility info",
                    "website": "https://211.org",
                    "phone": "211",
                    "source": "FALLBACK_HUD"
                } for _ in range(3)
            ] + fallback
