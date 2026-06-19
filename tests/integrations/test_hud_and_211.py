import pytest
from unittest.mock import MagicMock, patch
from app.integrations.hud.service import HudService
from app.integrations.api_211.service import Api211Service


@pytest.fixture
def mock_redis():
    with patch("app.integrations.hud.service.get_redis_client") as mock:
        client = MagicMock()
        client.get.return_value = None
        client.setex.return_value = None
        mock.return_value = client
        yield client


@pytest.fixture
def hud_service():
    with patch("app.integrations.hud.service.get_hud_client") as mock:
        yield HudService()


@pytest.fixture
def api_211_service():
    with patch("app.integrations.api_211.service.get_211_client") as mock:
        yield Api211Service()


@pytest.mark.asyncio
async def test_hud_search_success(mock_redis, hud_service):
    """Test successful HUD program search."""
    mock_response = {
        "programs": [
            {"program_name": "Test Program", "description": "Test Desc"}
        ]
    }
    
    with patch.object(hud_service.client, "get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = mock_response
        mock_get.return_value = mock_resp
        programs = await hud_service.search_programs(state="TX")
        assert len(programs) == 1
        assert programs[0]["name"] == "Test Program"


@pytest.mark.asyncio
async def test_hud_search_fallback(mock_redis, hud_service):
    """Test HUD search falls back to fallback data on failure."""
    with patch.object(hud_service.client, "get") as mock_get:
        mock_get.side_effect = Exception("HUD down!")
        programs = await hud_service.search_programs(state="TX")
        assert len(programs) > 0
        assert programs[-1]["name"] == "211 Texas"


@pytest.mark.asyncio
async def test_211_search_success(mock_redis, api_211_service):
    """Test successful 211 resource search."""
    mock_response = {
        "services": [
            {"organization_name": "Test Org", "service_description": "Test"}
        ]
    }
    
    with patch.object(api_211_service.client, "get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = mock_response
        mock_get.return_value = mock_resp
        services = await api_211_service.search_local_services(30, -97)
        assert len(services) == 1


@pytest.mark.asyncio
async def test_211_search_fallback(mock_redis, api_211_service):
    """Test 211 search falls back to fallback data on failure."""
    with patch.object(api_211_service.client, "get") as mock_get:
        mock_get.side_effect = Exception("211 down!")
        services = await api_211_service.search_local_services(30, -97)
        assert len(services) > 0
