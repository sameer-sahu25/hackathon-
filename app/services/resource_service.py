from typing import List, Optional
from app.models.resource import Resource, ResourceType
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import httpx
from app.config import settings
import logging

logger = logging.getLogger(__name__)


async def get_resources_nearby(
    db: AsyncSession,
    lat: float,
    lng: float,
    state: str,
    county: Optional[str] = None,
    income: Optional[int] = None,
    household_size: Optional[int] = None
) -> List[Resource]:
    result = await db.execute(
        select(Resource).where(
            and_(
                Resource.state == state.upper(),
                Resource.is_active == True
            )
        )
    )
    resources = list(result.scalars().all())
    # In a real implementation, we'd query HUD/211 APIs and calculate distance
    # For now, return DB resources
    return resources


async def get_resources_by_state(db: AsyncSession, state_code: str) -> List[Resource]:
    result = await db.execute(
        select(Resource).where(
            and_(
                Resource.state == state_code.upper(),
                Resource.is_active == True
            )
        )
    )
    return list(result.scalars().all())


async def get_resource_by_id(db: AsyncSession, resource_id: str) -> Optional[Resource]:
    result = await db.execute(select(Resource).where(Resource.id == resource_id))
    return result.scalar_one_or_none()


async def fetch_211_resources(lat: float, lng: float, state: str) -> List[dict]:
    # Mock implementation - in real life, query 211 API
    return []


async def fetch_hud_resources(state: str, county: str) -> List[dict]:
    # Mock implementation - in real life, query HUD API
    return []
