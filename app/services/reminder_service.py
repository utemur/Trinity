"""Сервис напоминаний: планирование и отправка."""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from zoneinfo import ZoneInfo

from app.db.models import Booking, BookingStatus, ScheduledReminder
from app.db.repo import BookingRepo, ScheduledReminderRepo


class ReminderService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def schedule_for_booking(self, booking: Booking, tz: str = "Asia/Tashkent") -> None:
        if booking.status != BookingStatus.CONFIRMED.value:
            return
        zone = ZoneInfo(tz)
        start = booking.start_dt
        if start.tzinfo is None:
            start = start.replace(tzinfo=ZoneInfo("UTC"))

        for delta, rtype in [(timedelta(hours=24), "24h"), (timedelta(hours=2), "2h")]:
            remind_at = start - delta
            if remind_at > datetime.now(zone):
                await ScheduledReminderRepo.create(
                    self.session, booking.id, remind_at, rtype
                )

    async def process_due_reminders(self, send_fn) -> int:
        reminders = await ScheduledReminderRepo.get_pending(self.session)
        sent = 0
        for rem in reminders:
            from sqlalchemy.orm import selectinload

            result = await self.session.execute(
                select(Booking).where(Booking.id == rem.booking_id).options(selectinload(Booking.service))
            )
            booking = result.scalar_one_or_none()
            if not booking or booking.status != BookingStatus.CONFIRMED.value:
                await ScheduledReminderRepo.mark_sent(self.session, rem.id)
                continue
            try:
                await send_fn(booking, rem.reminder_type)
                await ScheduledReminderRepo.mark_sent(self.session, rem.id)
                sent += 1
            except Exception:
                pass
        return sent

    async def rebuild_reminders_for_future_bookings(self, tz: str = "Asia/Tashkent") -> None:
        from app.db.models import Organization

        bookings = await BookingRepo.get_confirmed_future(self.session)
        for b in bookings:
            org_result = await self.session.execute(select(Organization).where(Organization.id == b.organization_id))
            org = org_result.scalar_one_or_none()
            tz_name = org.timezone if org else tz
            await self.schedule_for_booking(b, tz_name)
