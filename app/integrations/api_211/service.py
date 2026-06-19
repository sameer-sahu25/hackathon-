import time
from typing import List, Dict, Optional
from app.integrations.api_211.client import get_211_client
from app.integrations.api_211.mapper import normalize_211_result
from app.integrations.shared.logger import IntegrationLogger
from app.integrations.shared.circuit_breaker import get_api_211_circuit
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


class Api211Service:
    def __init__(self):
        self.client = get_211_client()

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
    async def search_local_services(
        self,
        lat: float,
        lng: float,
        county: Optional[str] = None,
        service_type: Optional[str] = None
    ) -> List[Dict]:
        start_time = time.time()
        cache_key = f"211:{county or 'all'}:{service_type or 'all'}"
        
        r = await get_redis_client()
        cached = await r.get(cache_key)
        if cached:
            IntegrationLogger.log_call(
                integration="api_211",
                method="search_local_services",
                latency_ms=(time.time() - start_time) * 1000,
                cache_hit=True,
                status="success"
            )
            return eval(cached.decode('utf-8'))
        
        try:
            async def _fetch_211():
                # Mock response in case 211 API is not available (replace with real endpoint when known)
                response = await self.client.get("/search", params={
                    "lat": lat,
                    "lng": lng,
                    "service_type": service_type
                })
                response.raise_for_status()
                data = response.json()
                return [normalize_211_result(s) for s in data.get("services", [])]
            
            circuit = get_api_211_circuit()
            services = await circuit(_fetch_211)
            
            await r.setex(cache_key, settings.CACHE_TTL_211, str(services))
            
            IntegrationLogger.log_call(
                integration="api_211",
                method="search_local_services",
                latency_ms=(time.time() - start_time) * 1000,
                cache_hit=False,
                status="success"
            )
            
            return services
        except Exception as e:
            sentry_sdk.capture_exception(e)
            # Fallback: return our fallback resources
            state = "TX"
            if lat > 36 and lng > -100: state = "IL"
            elif lat > 30 and lng < -110: state = "CA"
            elif lat > 25 and lng < -80: state = "FL"
            elif lat > 40 and lng < -75: state = "NY"
            return get_fallback_resources(state)
