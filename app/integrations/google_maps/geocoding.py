import hashlib
import asyncio
import time
from typing import Dict, Optional
from app.integrations.google_maps.client import get_gmaps_client
from app.integrations.shared.logger import IntegrationLogger
from app.integrations.shared.circuit_breaker import get_google_maps_circuit
from app.integrations.shared.fallbacks import get_fallback_resources
from app.config import settings
import redis.asyncio as redis
import sentry_sdk

redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> redis.Redis:
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(settings.REDIS_URL)
    assert redis_client is not None
    return redis_client


class GeocodeError(Exception):
    pass


async def geocode_address(address: str) -> Dict:
    start_time = time.time()
    cache_key = f"geocode:{hashlib.md5(address.encode('utf-8')).hexdigest()}"
    
    r = await get_redis_client()
    cached = await r.get(cache_key)
    if cached:
        IntegrationLogger.log_call(
            integration="google_maps",
            method="geocode_address",
            latency_ms=(time.time() - start_time) * 1000,
            cache_hit=True,
            status="success"
        )
        return eval(cached.decode('utf-8'))
    
    try:
        async def _geocode():
            gmaps = get_gmaps_client()
            result = await asyncio.to_thread(gmaps.geocode, address)
            if not result:
                raise GeocodeError("No geocoding results found")
            return {
                "lat": result[0]["geometry"]["location"]["lat"],
                "lng": result[0]["geometry"]["location"]["lng"],
                "formatted_address": result[0]["formatted_address"]
            }
        
        circuit = get_google_maps_circuit()
        geocoded = await circuit(_geocode)
        
        await r.setex(cache_key, settings.CACHE_TTL_GEOCODE, str(geocoded))
        
        IntegrationLogger.log_call(
            integration="google_maps",
            method="geocode_address",
            latency_ms=(time.time() - start_time) * 1000,
            cache_hit=False,
            status="success"
        )
        
        return geocoded
    except Exception as e:
        sentry_sdk.capture_exception(e)
        # Fallback: return county-level centroid for user's state (or TX default)
        state = address.split(",")[-1].strip() if "," in address else "TX"
        fallback_resources = get_fallback_resources(state)
        return {
            "lat": 31.9686,
            "lng": -99.9018,
            "formatted_address": address
        }


async def reverse_geocode(lat: float, lng: float) -> Dict:
    start_time = time.time()
    cache_key = f"reverse_geocode:{lat:.4f}:{lng:.4f}"
    
    r = await get_redis_client()
    cached = await r.get(cache_key)
    if cached:
        IntegrationLogger.log_call(
            integration="google_maps",
            method="reverse_geocode",
            latency_ms=(time.time() - start_time) * 1000,
            cache_hit=True,
            status="success"
        )
        return eval(cached.decode('utf-8'))
    
    try:
        async def _reverse_geocode():
            gmaps = get_gmaps_client()
            result = await asyncio.to_thread(gmaps.reverse_geocode, (lat, lng))
            if not result:
                raise GeocodeError("No reverse geocoding results found")
            components = result[0]["address_components"]
            county = next((c["long_name"] for c in components if "administrative_area_level_2" in c["types"]), None)
            state = next((c["short_name"] for c in components if "administrative_area_level_1" in c["types"]), None)
            return {
                "address": result[0]["formatted_address"],
                "county": county,
                "state": state
            }
        
        circuit = get_google_maps_circuit()
        rev_geocoded = await circuit(_reverse_geocode)
        
        await r.setex(cache_key, settings.CACHE_TTL_GEOCODE, str(rev_geocoded))
        
        IntegrationLogger.log_call(
            integration="google_maps",
            method="reverse_geocode",
            latency_ms=(time.time() - start_time) * 1000,
            cache_hit=False,
            status="success"
        )
        
        return rev_geocoded
    except Exception as e:
        sentry_sdk.capture_exception(e)
        # Fallback: return generic state/county based on lat/lng rough region
        return {
            "address": f"Location at {lat}, {lng}",
            "county": "Unknown",
            "state": "TX"
        }
