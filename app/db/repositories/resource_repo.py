from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, insert, update as sa_update
from typing import Optional, List
from app.db.repositories.base_repo import BaseRepository
from app.db.models.resource import Resource, ResourceType


class ResourceRepository(BaseRepository[Resource]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Resource)

    async def get_by_state(
        self,
        state: str,
        resource_type: Optional[str] = None
    ) -> List[Resource]:
        stmt = select(Resource).where(
            Resource.state == state,
            Resource.is_active == True,
            Resource.is_deleted == False
        )
        if resource_type:
            stmt = stmt.where(Resource.resource_type == resource_type)
        stmt = stmt.order_by(Resource.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_nearby(
        self,
        lat: float,
        lng: float,
        radius_miles: float = 25.0,
        resource_type: Optional[str] = None
    ) -> List[Resource]:
        # Haversine formula in SQL
        haversine = (
            3959 * func.acos(
                func.cos(func.radians(lat)) * func.cos(func.radians(Resource.latitude)) *
                func.cos(func.radians(Resource.longitude) - func.radians(lng)) +
                func.sin(func.radians(lat)) * func.sin(func.radians(Resource.latitude))
            )
        ).label("distance")

        stmt = (
            select(Resource, haversine)
            .where(
                Resource.is_active == True,
                Resource.is_deleted == False,
                Resource.latitude.is_not(None),
                Resource.longitude.is_not(None),
                haversine <= radius_miles
            )
            .order_by(haversine)
        )
        if resource_type:
            stmt = stmt.where(Resource.resource_type == resource_type)
        
        result = await self.session.execute(stmt)
        resources = []
        for row in result.all():
            resource = row[0]
            resources.append(resource)
        return resources

    async def get_by_eligibility(
        self,
        state: str,
        income_monthly: int,
        household_size: int,
        serves_undocumented: bool = False
    ) -> List[Resource]:
        stmt = select(Resource).where(
            Resource.state == state,
            Resource.is_active == True,
            Resource.is_deleted == False
        )
        
        # Filter by household size if applicable
        stmt = stmt.where(
            (Resource.max_household_size.is_(None)) | 
            (Resource.max_household_size >= household_size)
        )
        
        # Filter by serves_undocumented
        if serves_undocumented:
            stmt = stmt.where(Resource.serves_undocumented == True)
        
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def bulk_upsert(self, resources: List[dict]) -> int:
        upserted_count = 0
        for resource_data in resources:
            external_id = resource_data.get("external_id")
            if not external_id:
                continue
                
            # Check if resource exists
            stmt = select(Resource).where(
                Resource.external_id == external_id,
                Resource.source == resource_data.get("source"),
                Resource.is_deleted == False
            )
            result = await self.session.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update existing resource
                resource_data["updated_at"] = func.now()
                for key, value in resource_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                upserted_count += 1
            else:
                # Create new resource
                new_resource = Resource(**resource_data)
                self.session.add(new_resource)
                upserted_count += 1
        
        await self.session.flush()
        return upserted_count
