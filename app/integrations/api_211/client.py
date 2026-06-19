from app.integrations.shared.http_client import get_http_client
from app.config import settings

def get_211_client():
    return get_http_client(
        timeout=6.0,
        base_url="https://api.211.org",
        headers={"Authorization": f"Bearer {settings.API_211_KEY}"}
    )
