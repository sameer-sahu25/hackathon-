from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from typing import Optional, List, Dict
import uuid
from app.db.repositories.base_repo import BaseRepository
from app.db.models.intake import Intake


class IntakeRepository(BaseRepository[Intake]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Intake)

    async def get_by_user(self, user_id: uuid.UUID) -> List[Intake]:
        stmt = (
            select(Intake)
            .where(Intake.user_id == user_id, Intake.is_deleted == False)
            .options(selectinload(Intake.action_plans))
            .order_by(Intake.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_latest_by_user(self, user_id: uuid.UUID) -> Optional[Intake]:
        stmt = (
            select(Intake)
            .where(Intake.user_id == user_id, Intake.is_deleted == False)
            .order_by(Intake.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_state(self, state: str, skip: int = 0, limit: int = 100) -> List[Intake]:
        stmt = (
            select(Intake)
            .where(Intake.state == state, Intake.is_deleted == False)
            .order_by(Intake.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_critical_intakes(self) -> List[Intake]:
        stmt = (
            select(Intake)
            .where(
                Intake.urgency_days <= 2,
                Intake.has_received_notice == True,
                Intake.is_deleted == False
            )
            .options(selectinload(Intake.action_plans))
            .order_by(Intake.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_stats_by_state(self) -> Dict:
        stmt = (
            select(Intake.state, func.count(Intake.id))
            .where(Intake.is_deleted == False)
            .group_by(Intake.state)
            .order_by(func.count(Intake.id).desc())
        )
        result = await self.session.execute(stmt)
        return {state: count for state, count in result.all()}

    async def get_domestic_violence_intakes(self) -> List[Intake]:
        stmt = (
            select(Intake)
            .where(
                Intake.is_domestic_violence == True,
                Intake.is_deleted == False
            )
            .order_by(Intake.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
