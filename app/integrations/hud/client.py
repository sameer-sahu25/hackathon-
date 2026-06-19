from app.integrations.shared.http_client import get_http_client
from app.config import settings

def get_hud_client():
    return get_http_client(
        timeout=8.0,
        base_url="https://www.hud.gov",
        headers={"Authorization": f"Bearer {settings.HUD_API_KEY}"}
    )
