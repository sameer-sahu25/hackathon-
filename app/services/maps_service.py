import httpx
from app.config import settings
import logging

logger = logging.getLogger(__name__)


async def geocode_address(address: str) -> tuple[float, float] | None:
    """Geocode an address to lat/lng using Google Maps API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={
                    "address": address,
                    "key": settings.GOOGLE_MAPS_API_KEY
                }
            )
            data = response.json()
            if data["status"] == "OK":
                location = data["results"][0]["geometry"]["location"]
                return (location["lat"], location["lng"])
    except Exception as e:
        logger.error(f"Geocoding failed: {e}")
    return None


async def get_distance(origin_lat: float, origin_lng: float, dest_lat: float, dest_lng: float) -> float:
    """Calculate distance in miles between two coordinates using Haversine formula as fallback"""
    import math
    R = 3958.8  # Earth radius in miles
    dlat = math.radians(dest_lat - origin_lat)
    dlng = math.radians(dest_lng - origin_lng)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(origin_lat)) * math.cos(math.radians(dest_lat)) * math.sin(dlng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c
