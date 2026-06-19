from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import Optional, List, Dict
import uuid
from datetime import datetime, UTC, timedelta
from app.db.repositories.base_repo import BaseRepository
from app.db.models.action_plan import ActionPlan, UrgencyLevel


class ActionPlanRepository(BaseRepository[ActionPlan]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, ActionPlan)

    async def get_by_intake(self, intake_id: uuid.UUID) -> Optional[ActionPlan]:
        stmt = select(ActionPlan).where(
            ActionPlan.intake_id == intake_id, ActionPlan.is_deleted == False
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_by_user(self, user_id: uuid.UUID) -> Optional[ActionPlan]:
        stmt = (
            select(ActionPlan)
            .where(ActionPlan.user_id == user_id, ActionPlan.is_deleted == False)
            .order_by(ActionPlan.generated_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_critical_plans(self) -> List[ActionPlan]:
        cutoff = datetime.now(UTC) - timedelta(days=1)
        stmt = (
            select(ActionPlan)
            .where(
                ActionPlan.urgency_level == UrgencyLevel.CRITICAL,
                ActionPlan.generated_at >= cutoff,
                ActionPlan.is_deleted == False
            )
            .order_by(ActionPlan.generated_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_escalated_plans(self) -> List[ActionPlan]:
        stmt = (
            select(ActionPlan)
            .where(
                ActionPlan.escalation_flag == True,
                ActionPlan.is_deleted == False
            )
            .order_by(ActionPlan.generated_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_avg_confidence_by_state(self) -> Dict:
        stmt = (
            select(ActionPlan.state, func.avg(ActionPlan.confidence_score))
            .where(ActionPlan.is_deleted == False)
            .group_by(ActionPlan.state)
        )
        result = await self.session.execute(stmt)
        return {state: float(avg) for state, avg in result.all()}

    async def get_ai_metrics(self) -> Dict:
        avg_latency = select(func.avg(ActionPlan.generation_latency_ms)).where(
            ActionPlan.is_deleted == False
        )
        avg_tokens_input = select(func.avg(ActionPlan.tokens_input)).where(
            ActionPlan.is_deleted == False, ActionPlan.tokens_input.isnot(None)
        )
        avg_tokens_output = select(func.avg(ActionPlan.tokens_output)).where(
            ActionPlan.is_deleted == False, ActionPlan.tokens_output.isnot(None)
        )
        cache_hits = select(func.count(ActionPlan.id)).where(
            ActionPlan.is_deleted == False, ActionPlan.cache_hit == True
        )
        retries = select(func.count(ActionPlan.id)).where(
            ActionPlan.is_deleted == False, ActionPlan.retries_needed > 0
        )

        results = await self.session.execute(
            select(
                avg_latency.scalar_subquery(),
                avg_tokens_input.scalar_subquery(),
                avg_tokens_output.scalar_subquery(),
                cache_hits.scalar_subquery(),
                retries.scalar_subquery(),
            )
        )

        (avg_latency_val, avg_tok_in, avg_tok_out, cache_hit_count, retry_count) = results.one()

        return {
            "avg_generation_latency_ms": float(avg_latency_val) if avg_latency_val else 0,
            "avg_tokens_input": float(avg_tok_in) if avg_tok_in else 0,
            "avg_tokens_output": float(avg_tok_out) if avg_tok_out else 0,
            "cache_hits_count": int(cache_hit_count),
            "retries_needed_count": int(retry_count)
        }
