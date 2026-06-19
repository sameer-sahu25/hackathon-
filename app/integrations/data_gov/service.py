import time
from typing import List, Dict, Optional
from app.integrations.data_gov.client import get_data_gov_client
from app.integrations.shared.logger import IntegrationLogger
from app.integrations.shared.circuit_breaker import get_data_gov_circuit
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


class DataGovService:
    def __init__(self):
        self.client = get_data_gov_client()

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
    async def get_federal_housing_rules(self, program_type: Optional[str] = None) -> List[Dict]:
        start_time = time.time()
        cache_key = f"datagov:{program_type or 'all'}"
        
        r = await get_redis_client()
        cached = await r.get(cache_key)
        if cached:
            IntegrationLogger.log_call(
                integration="data_gov",
                method="get_federal_housing_rules",
                latency_ms=(time.time() - start_time) * 1000,
                cache_hit=True,
                status="success"
            )
            return eval(cached.decode('utf-8'))
        
        try:
            async def _fetch_datagov():
                # Mock response in case Data.gov API is not available (replace with real endpoint when known)
                response = await self.client.get("/action/package_search", params={
                    "q": "housing rules"
                })
                response.raise_for_status()
                data = response.json()
                
                rules = []
                for result in data.get("result", {}).get("results", []):
                    rules.append({
                        "title": result.get("title", ""),
                        "description": result.get("notes", ""),
                        "url": result.get("url"),
                        "source": "DATA_GOV"
                    })
                return rules
            
            circuit = get_data_gov_circuit()
            rules = await circuit(_fetch_datagov)
            
            await r.setex(cache_key, settings.CACHE_TTL_DATAGOV, str(rules))
            
            IntegrationLogger.log_call(
                integration="data_gov",
                method="get_federal_housing_rules",
                latency_ms=(time.time() - start_time) * 1000,
                cache_hit=False,
                status="success"
            )
            
            return rules
        except Exception as e:
            sentry_sdk.capture_exception(e)
            # Fallback: return basic federal housing information
            return [
                {
                    "title": "Federal Housing Rights",
                    "description": "You have the right to safe housing, fair treatment, and access to legal assistance. Contact 211 for details.",
                    "url": "https://www.hud.gov",
                    "source": "FALLBACK_DATAGOV"
                },
                {
                    "title": "Emergency Rental Assistance",
                    "description": "Emergency rental aid may be available - call 211 for information.",
                    "url": "https://211.org",
                    "source": "FALLBACK_DATAGOV"
                }
            ]
