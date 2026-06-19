from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import Optional, List, Dict
import uuid
from datetime import datetime, UTC, date
from app.db.repositories.base_repo import BaseRepository
from app.db.models.progress import ProgressStep, StepOutcome


class ProgressRepository(BaseRepository[ProgressStep]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ProgressStep)

    async def get_by_action_plan(self, action_plan_id: uuid.UUID) -> List[ProgressStep]:
        stmt = select(ProgressStep).where(
            ProgressStep.action_plan_id == action_plan_id,
            ProgressStep.is_deleted == False
        ).order_by(ProgressStep.step_number)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_completion_rate(self, action_plan_id: uuid.UUID) -> Dict:
        total_stmt = select(func.count(ProgressStep.id)).where(
            ProgressStep.action_plan_id == action_plan_id,
            ProgressStep.is_deleted == False
        )
        completed_stmt = select(func.count(ProgressStep.id)).where(
            ProgressStep.action_plan_id == action_plan_id,
            ProgressStep.is_completed == True,
            ProgressStep.is_deleted == False
        )
        total_result = await self.session.execute(total_stmt)
        completed_result = await self.session.execute(completed_stmt)
        
        total = total_result.scalar() or 0
        completed = completed_result.scalar() or 0
        percentage = (completed / total * 100) if total > 0 else 0
        
        return {
            "total": total,
            "completed": completed,
            "percentage": round(percentage, 2)
        }

    async def get_next_step(self, action_plan_id: uuid.UUID) -> Optional[ProgressStep]:
        stmt = select(ProgressStep).where(
            ProgressStep.action_plan_id == action_plan_id,
            ProgressStep.is_completed == False,
            ProgressStep.skipped == False,
            ProgressStep.is_deleted == False
        ).order_by(ProgressStep.step_number).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_complete(self, step_id: uuid.UUID, notes: Optional[str] = None) -> ProgressStep:
        step = await self.get_by_id(step_id)
        if step:
            step.is_completed = True
            step.completed_at = datetime.now(UTC)
            step.outcome = StepOutcome.COMPLETED
            if notes:
                step.notes = notes
            step.updated_at = datetime.now(UTC)
            await self.session.flush()
            await self.session.refresh(step)
        return step

    async def get_outcomes_summary(self) -> Dict:
        stmt = select(
            ProgressStep.outcome,
            func.count(ProgressStep.id)
        ).where(
            ProgressStep.is_deleted == False
        ).group_by(ProgressStep.outcome)
        result = await self.session.execute(stmt)
        return {str(outcome): count for outcome, count in result.all()}

    async def get_resolved_count_today(self) -> int:
        today_start = datetime.combine(date.today(), datetime.min.time(), tzinfo=UTC)
        stmt = select(func.count(ProgressStep.id)).where(
            ProgressStep.outcome == StepOutcome.COMPLETED,
            ProgressStep.completed_at >= today_start,
            ProgressStep.is_deleted == False
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0
