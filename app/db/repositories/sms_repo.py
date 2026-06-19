from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional, List
import uuid
from datetime import datetime, UTC
from app.db.repositories.base_repo import BaseRepository
from app.db.models.sms_reminder import SMSReminder, SMSStatus


class SMSRepository(BaseRepository[SMSReminder]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, SMSReminder)

    async def get_pending_scheduled(self, before_datetime: datetime) -> List[SMSReminder]:
        stmt = select(SMSReminder).where(
            SMSReminder.status == SMSStatus.PENDING,
            SMSReminder.scheduled_at <= before_datetime,
            SMSReminder.is_deleted == False
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_status(self, sms_id: uuid.UUID, status: SMSStatus, **kwargs) -> Optional[SMSReminder]:
        sms = await self.get_by_id(sms_id)
        if not sms:
            return None
        
        sms.status = status
        if status == SMSStatus.SENT:
            sms.sent_at = datetime.now(UTC)
        if status == SMSStatus.DELIVERED:
            sms.delivered_at = datetime.now(UTC)
        
        for key, value in kwargs.items():
            if hasattr(sms, key):
                setattr(sms, key, value)
        
        await self.session.flush()
        await self.session.refresh(sms)
        return sms
