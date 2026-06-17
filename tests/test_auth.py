import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_anonymous_user(client: AsyncClient):
    """Test creating an anonymous user session"""
    response = await client.post("/api/v1/auth/anonymous", json={"language": "EN"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration"""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "testpass123", "language": "EN"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
