import asyncio
import time
from typing import Dict, List, Optional, Tuple
from app.integrations.google_maps.client import get_gmaps_client
from app.integrations.shared.logger import IntegrationLogger
from app.config import settings
import redis.asyncio as redis
import sentry_sdk

redis_client: Optional[redis.Redis] = None


async def get_redis_client():
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(settings.REDIS_URL)
    return redis_client


async def get_distance_matrix(
    origin: Tuple[float, float],
    destinations: List[Tuple[float, float]]
) -> List[Dict]:
    start_time = time.time()
    dest_key = "_".join([f"{lat:.2f},{lng:.2f}" for lat, lng in destinations[:5]])
    cache_key = f"distance:{origin[0]:.2f},{origin[1]:.2f}:{dest_key}"
    
    r = await get_redis_client()
    cached = await r.get(cache_key)
    if cached:
        IntegrationLogger.log_call(
            integration="google_maps",
            method="get_distance_matrix",
            latency_ms=(time.time() - start_time) * 1000,
            cache_hit=True,
            status="success"
        )
        return eval(cached.decode('utf-8'))
    
    try:
        gmaps = get_gmaps_client()
        result = await asyncio.to_thread(
            gmaps.distance_matrix,
            origins=[origin],
            destinations=destinations[:25]
        )
        
        distances = []
        rows = result.get("rows", [])
        if rows:
            elements = rows[0].get("elements", [])
            for i, elem in enumerate(elements):
                dist_m = elem.get("distance", {}).get("value", 0)
                dur_s = elem.get("duration", {}).get("value", 0)
                distances.append({
                    "destination": destinations[i],
                    "distance_miles": dist_m / 1609.34,
                    "duration_minutes": dur_s / 60
                })
        
        await r.setex(cache_key, 30 * 60, str(distances))
        
        IntegrationLogger.log_call(
            integration="google_maps",
            method="get_distance_matrix",
            latency_ms=(time.time() - start_time) * 1000,
            cache_hit=False,
            status="success"
        )
        
        return distances
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return []
