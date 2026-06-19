from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import Optional, List, Dict
import uuid
from datetime import datetime, UTC, timedelta
from app.db.models.analytics import AnalyticsEvent


class AnalyticsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_event(
        self,
        event_type: str,
        user_id: Optional[uuid.UUID] = None,
        properties: Dict = {}
    ) -> AnalyticsEvent:
        event = AnalyticsEvent(
            event_type=event_type,
            user_id=user_id,
            properties=properties,
            created_at=datetime.now(UTC)
        )
        self.session.add(event)
        await self.session.flush()
        await self.session.refresh(event)
        return event

    async def get_impact_metrics(self) -> Dict:
        # Total users helped (unique users with intake)
        total_users_stmt = select(func.count(func.distinct(AnalyticsEvent.user_id))).where(
            AnalyticsEvent.user_id.is_not(None)
        )
        
        # Evictions avoided
        evictions_avoided_stmt = select(func.count(AnalyticsEvent.id)).where(
            AnalyticsEvent.event_type == "EVICTION_AVOIDED"
        )
        
        # Action plans generated
        plans_generated_stmt = select(func.count(AnalyticsEvent.id)).where(
            AnalyticsEvent.event_type == "ACTION_PLAN_GENERATED"
        )
        
        # SMS reminders sent
        sms_sent_stmt = select(func.count(AnalyticsEvent.id)).where(
            AnalyticsEvent.event_type == "SMS_SENT"
        )
        
        # PDFs downloaded
        pdfs_downloaded_stmt = select(func.count(AnalyticsEvent.id)).where(
            AnalyticsEvent.event_type == "PDF_DOWNLOADED"
        )
        
        # Resources clicked
        resources_clicked_stmt = select(func.count(AnalyticsEvent.id)).where(
            AnalyticsEvent.event_type == "RESOURCE_CLICKED"
        )
        
        # Top states by usage
        top_states_stmt = select(
            AnalyticsEvent.state,
            func.count(AnalyticsEvent.id).label("count")
        ).where(
            AnalyticsEvent.state.is_not(None)
        ).group_by(AnalyticsEvent.state).order_by(func.count(AnalyticsEvent.id).desc()).limit(5)
        
        # Urgency distribution
        urgency_distribution_stmt = select(
            AnalyticsEvent.urgency_level,
            func.count(AnalyticsEvent.id).label("count")
        ).where(
            AnalyticsEvent.urgency_level.is_not(None)
        ).group_by(AnalyticsEvent.urgency_level)
        
        # Execute all queries
        total_users = (await self.session.execute(total_users_stmt)).scalar() or 0
        evictions_avoided = (await self.session.execute(evictions_avoided_stmt)).scalar() or 0
        action_plans_generated = (await self.session.execute(plans_generated_stmt)).scalar() or 0
        sms_sent = (await self.session.execute(sms_sent_stmt)).scalar() or 0
        pdfs_downloaded = (await self.session.execute(pdfs_downloaded_stmt)).scalar() or 0
        resources_clicked = (await self.session.execute(resources_clicked_stmt)).scalar() or 0
        top_states = [{"state": s, "count": c} for s, c in (await self.session.execute(top_states_stmt)).all()]
        
        urgency_results = (await self.session.execute(urgency_distribution_stmt)).all()
        total_urgency = sum(c for _, c in urgency_results) if urgency_results else 0
        urgency_distribution = {
            u: round(c / total_urgency * 100, 2) 
            for u, c in urgency_results
        } if total_urgency > 0 else {}
        
        return {
            "total_users_helped": total_users,
            "evictions_avoided": evictions_avoided,
            "action_plans_generated": action_plans_generated,
            "sms_reminders_sent": sms_sent,
            "pdfs_downloaded": pdfs_downloaded,
            "resources_clicked": resources_clicked,
            "top_states_by_usage": top_states,
            "urgency_distribution": urgency_distribution
        }

    async def get_daily_stats(self, days: int = 7) -> List[Dict]:
        start_date = datetime.now(UTC) - timedelta(days=days)
        
        stmt = select(
            func.date_trunc('day', AnalyticsEvent.created_at).label('day'),
            func.count(AnalyticsEvent.id).label('total_events'),
            func.count(func.filter(AnalyticsEvent.event_type == 'ACTION_PLAN_GENERATED')).label('plans_created'),
            func.count(func.filter(AnalyticsEvent.event_type == 'RESOURCE_CLICKED')).label('resources_used')
        ).where(
            AnalyticsEvent.created_at >= start_date
        ).group_by('day').order_by('day')
        
        result = await self.session.execute(stmt)
        return [
            {
                "date": day.date().isoformat(),
                "total_events": total,
                "plans_created": plans,
                "resources_used": resources
            }
            for day, total, plans, resources in result.all()
        ]
