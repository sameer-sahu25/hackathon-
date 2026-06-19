import pytest
from unittest.mock import MagicMock, patch
from app.integrations.google_maps import geocoding, places


@pytest.fixture
def mock_redis():
    with patch("app.integrations.google_maps.geocoding.get_redis_client") as mock:
        client = MagicMock()
        client.get.return_value = None
        client.setex.return_value = None
        mock.return_value = client
        yield client


@pytest.fixture
def mock_gmaps_client():
    with patch("app.integrations.google_maps.geocoding.get_gmaps_client") as mock:
        yield mock


@pytest.mark.asyncio
async def test_geocode_address_success(mock_redis, mock_gmaps_client):
    """Test successful geocoding."""
    mock_result = [
        {
            "geometry": {"location": {"lat": 30.2672, "lng": -97.7431}},
            "formatted_address": "Austin, TX, USA"
        }
    ]
    
    with patch.object(mock_gmaps_client(), "geocode", return_value=mock_result):
        result = await geocoding.geocode_address("Austin, TX")
        assert result["lat"] == 30.2672
        assert result["lng"] == -97.7431


@pytest.mark.asyncio
async def test_geocode_address_fallback(mock_redis, mock_gmaps_client):
    """Test that geocoding falls back to default location on failure."""
    with patch.object(mock_gmaps_client(), "geocode", side_effect=Exception("Maps down!")):
        result = await geocoding.geocode_address("Austin, TX")
        assert result["lat"] == 31.9686  # TX default
        assert result["lng"] == -99.9018


@pytest.mark.asyncio
async def test_find_nearby_resources_success(mock_redis):
    """Test nearby resources search."""
    with patch("app.integrations.google_maps.places.get_gmaps_client") as mock_gmaps:
        mock_result = {
            "results": [
                {
                    "name": "Test Resource",
                    "vicinity": "123 St",
                    "place_id": "test_place"
                }
            ]
        }
        mock_gmaps().places_nearby.return_value = mock_result
        resources = await places.find_nearby_resources(30.2672, -97.7431, "shelter")
        assert len(resources) == 1
        assert resources[0]["name"] == "Test Resource"


@pytest.mark.asyncio
async def test_find_nearby_resources_fallback(mock_redis):
    """Test that nearby resources fall back to hardcoded list on failure."""
    with patch("app.integrations.google_maps.places.get_gmaps_client") as mock_gmaps:
        mock_gmaps().places_nearby.side_effect = Exception("Maps down!")
        resources = await places.find_nearby_resources(30.2672, -97.7431, "shelter")
        assert len(resources) > 0
        assert resources[0]["name"] == "211 Texas"
