import asyncio
import time
from typing import Dict, List, Optional
from app.integrations.google_maps.client import get_gmaps_client
from app.integrations.shared.logger import IntegrationLogger
from app.integrations.shared.circuit_breaker import get_google_maps_circuit
from app.integrations.shared.fallbacks import get_fallback_resources
from app.config import settings
import redis.asyncio as redis
import sentry_sdk

redis_client: Optional[redis.Redis] = None


async def get_redis_client():
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(settings.REDIS_URL)
    return redis_client


async def find_nearby_resources(
    lat: float,
    lng: float,
    resource_type: str,
    radius_miles: float = 25.0
) -> List[Dict]:
    start_time = time.time()
    radius_meters = radius_miles * 1609.34
    cache_key = f"places:{lat:.2f}:{lng:.2f}:{resource_type}"
    
    r = await get_redis_client()
    cached = await r.get(cache_key)
    if cached:
        IntegrationLogger.log_call(
            integration="google_maps",
            method="find_nearby_resources",
            latency_ms=(time.time() - start_time) * 1000,
            cache_hit=True,
            status="success"
        )
        return eval(cached.decode('utf-8'))
    
    try:
        async def _find_places():
            gmaps = get_gmaps_client()
            result = await asyncio.to_thread(
                gmaps.places_nearby,
                location=(lat, lng),
                radius=radius_meters,
                keyword=resource_type
            )
            places = []
            for place in result.get("results", []):
                places.append({
                    "name": place.get("name"),
                    "address": place.get("vicinity"),
                    "place_id": place.get("place_id"),
                    "rating": place.get("rating"),
                    "open_now": place.get("opening_hours", {}).get("open_now"),
                    "location": place.get("geometry", {}).get("location")
                })
            return places
        
        circuit = get_google_maps_circuit()
        places = await circuit(_find_places)
        
        await r.setex(cache_key, settings.CACHE_TTL_PLACES, str(places))
        
        IntegrationLogger.log_call(
            integration="google_maps",
            method="find_nearby_resources",
            latency_ms=(time.time() - start_time) * 1000,
            cache_hit=False,
            status="success"
        )
        
        return places
    except Exception as e:
        sentry_sdk.capture_exception(e)
        # Fallback: return hardcoded 211 and national resources
        # Roughly map state based on lat/lng
        state = "TX"
        if lat > 36 and lng > -100: state = "IL"
        elif lat > 30 and lng < -110: state = "CA"
        elif lat > 25 and lng < -80: state = "FL"
        elif lat > 40 and lng < -75: state = "NY"
        return get_fallback_resources(state)


async def get_place_details(place_id: str) -> Dict:
    start_time = time.time()
    cache_key = f"place_details:{place_id}"
    
    r = await get_redis_client()
    cached = await r.get(cache_key)
    if cached:
        IntegrationLogger.log_call(
            integration="google_maps",
            method="get_place_details",
            latency_ms=(time.time() - start_time) * 1000,
            cache_hit=True,
            status="success"
        )
        return eval(cached.decode('utf-8'))
    
    try:
        async def _get_details():
            gmaps = get_gmaps_client()
            result = await asyncio.to_thread(gmaps.place, place_id)
            place = result.get("result", {})
            return {
                "name": place.get("name"),
                "address": place.get("formatted_address"),
                "phone": place.get("formatted_phone_number"),
                "website": place.get("website"),
                "hours": place.get("opening_hours", {}).get("weekday_text")
            }
        
        circuit = get_google_maps_circuit()
        details = await circuit(_get_details)
        
        await r.setex(cache_key, settings.CACHE_TTL_PLACE_DETAILS, str(details))
        
        IntegrationLogger.log_call(
            integration="google_maps",
            method="get_place_details",
            latency_ms=(time.time() - start_time) * 1000,
            cache_hit=False,
            status="success"
        )
        
        return details
    except Exception as e:
        sentry_sdk.capture_exception(e)
        # Fallback: return minimal info
        return {
            "name": "Local Resource",
            "address": "Call 211 for details",
            "phone": "211",
            "website": "https://211.org",
            "hours": None
        }
