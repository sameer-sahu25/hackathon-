from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sa_update, delete as sa_delete, func
from typing import TypeVar, Generic, Type, Optional, List, Dict
import uuid
from datetime import datetime, UTC
from app.db.models.base_model import BaseModel


ModelType = TypeVar("ModelType", bound=BaseModel)


class BaseRepository(Generic[ModelType]):
    def __init__(self, session: AsyncSession, model: Type[ModelType]):
        self.session = session
        self.model = model

    async def get_by_id(self, id: uuid.UUID) -> Optional[ModelType]:
        stmt = select(self.model).where(self.model.id == id, self.model.is_deleted == False)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100, order_by: str = "created_at") -> List[ModelType]:
        stmt = (
            select(self.model)
            .where(self.model.is_deleted == False)
            .order_by(getattr(self.model, order_by).desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, data: Dict) -> ModelType:
        instance = self.model(**data)
        self.session.add(instance)
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def update(self, id: uuid.UUID, data: Dict) -> Optional[ModelType]:
        instance = await self.get_by_id(id)
        if not instance:
            return None
        
        data["updated_at"] = datetime.now(UTC)
        for key, value in data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        
        await self.session.flush()
        await self.session.refresh(instance)
        return instance

    async def soft_delete(self, id: uuid.UUID) -> bool:
        instance = await self.get_by_id(id)
        if not instance:
            return False
        
        instance.soft_delete()
        await self.session.flush()
        return True

    async def hard_delete(self, id: uuid.UUID) -> bool:
        instance = await self.get_by_id(id)
        if not instance:
            return False
        
        await self.session.delete(instance)
        await self.session.flush()
        return True

    async def count(self, filters: Dict = {}) -> int:
        stmt = select(func.count(self.model.id)).where(self.model.is_deleted == False)
        for key, value in filters.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)
        
        result = await self.session.execute(stmt)
        return result.scalar()
