from app.integrations.shared.http_client import get_http_client
from app.config import settings


def get_data_gov_client():
    return get_http_client(
        timeout=8.0,
        base_url="https://catalog.data.gov/api/3"
    )
