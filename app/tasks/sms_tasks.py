from celery import shared_task
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.tasks.celery_app import celery_app
from app.models.sms_reminder import SmsReminder, SmsStatus
from app.db.session import AsyncSessionLocal
from app.services.sms_service import send_sms, build_sms_message
from app.config import settings
from sqlalchemy import select, delete
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_sms_reminder_task(reminder_id: str):
    """Background task to send a single SMS reminder"""
    async def _send():
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(SmsReminder).where(SmsReminder.id == UUID(reminder_id))
            )
            reminder = result.scalar_one_or_none()
            if not reminder or reminder.status != SmsStatus.PENDING:
                return

            try:
                twilio_sid = await send_sms(reminder.phone_number, reminder.message_body)
                if twilio_sid:
                    reminder.sent_at = datetime.utcnow()
                    reminder.status = SmsStatus.SENT
                    reminder.twilio_sid = twilio_sid
                else:
                    reminder.status = SmsStatus.FAILED
                await db.commit()
            except Exception as e:
                logger.error(f"Failed to send SMS reminder {reminder_id}: {e}")
                reminder.status = SmsStatus.FAILED
                await db.commit()

    import asyncio
    asyncio.run(_send())


@shared_task
def schedule_sms_reminders_task(intake_id: str, user_id: str, phone_number: str, deadline_date: str):
    """Schedule multiple SMS reminders (7 days, 3 days, 24 hours, morning of)"""
    async def _schedule():
        deadline = datetime.fromisoformat(deadline_date)
        reminder_times = [
            deadline - timedelta(days=7),
            deadline - timedelta(days=3),
            deadline - timedelta(hours=24),
            deadline.replace(hour=9, minute=0, second=0)  # 9 AM day of deadline
        ]

        async with AsyncSessionLocal() as db:
            # Delete existing pending reminders for this intake
            await db.execute(
                delete(SmsReminder).where(
                    (SmsReminder.intake_id == UUID(intake_id)) &
                    (SmsReminder.status == SmsStatus.PENDING)
                )
            )

            for scheduled_time in reminder_times:
                if scheduled_time > datetime.utcnow():
                    message = build_sms_message(deadline)
                    reminder = SmsReminder(
                        user_id=UUID(user_id),
                        phone_number=phone_number,
                        intake_id=UUID(intake_id),
                        message_body=message,
                        scheduled_at=scheduled_time,
                        status=SmsStatus.PENDING
                    )
                    db.add(reminder)
                    await db.flush()

                    # Schedule Celery task
                    send_sms_reminder_task.apply_async(
                        args=[str(reminder.id)],
                        eta=scheduled_time
                    )

            await db.commit()

    import asyncio
    asyncio.run(_schedule())


@shared_task
def cleanup_expired_sessions_task():
    """Clean up old sessions (run daily via Celery Beat)"""
    from app.models.user import User
    from datetime import datetime, timedelta
    from sqlalchemy import delete

    async def _cleanup():
        cutoff = datetime.utcnow() - timedelta(days=90)
        async with AsyncSessionLocal() as db:
            await db.execute(
                delete(User).where(
                    (User.is_anonymous == True) &
                    (User.last_active_at < cutoff)
                )
            )
            await db.commit()

    import asyncio
    asyncio.run(_cleanup())
