import googlemaps
from app.config import settings
from typing import Optional

_gmaps_client: Optional[googlemaps.Client] = None


def get_gmaps_client() -> googlemaps.Client:
    global _gmaps_client
    if _gmaps_client is None:
        _gmaps_client = googlemaps.Client(key=settings.GOOGLE_MAPS_API_KEY, timeout=5)
    return _gmaps_client
