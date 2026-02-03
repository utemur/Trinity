"""Сервис бронирований: слоты, создание, подтверждение."""

from datetime import date, datetime, timedelta
from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from zoneinfo import ZoneInfo

from app.db.models import AvailabilityRule, BlackoutDate, Booking, BookingStatus, Service
from app.db.repo import (
    AvailabilityRuleRepo,
    BlackoutDateRepo,
    BookingRepo,
    OrganizationRepo,
    ServiceRepo,
    SubscriptionRepo,
)


class BookingService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_available_slots(
        self, organization_id: int, service_id: int, target_date: date, tz: str
    ) -> list[datetime]:
        org = await OrganizationRepo.get_by_id(self.session, organization_id)
        if not org:
            return []

        service = await ServiceRepo.get_by_id(self.session, service_id)
        if not service or not service.is_active:
            return []

        rules = await AvailabilityRuleRepo.get_by_org(self.session, organization_id)
        weekday = target_date.weekday()
        day_rules = [r for r in rules if r.weekday == weekday]
        if not day_rules:
            return []

        zone = ZoneInfo(tz)
        slots: list[datetime] = []

        for rule in day_rules:
            current = datetime.combine(target_date, rule.start_time, tzinfo=zone)
            end_dt = datetime.combine(target_date, rule.end_time, tzinfo=zone)
            step = timedelta(minutes=rule.slot_step_minutes)

            while current + timedelta(minutes=service.duration_minutes) <= end_dt:
                slot_end = current + timedelta(minutes=service.duration_minutes)
                slots.append(current)
                current += step

        blackouts = await BlackoutDateRepo.get_by_org(self.session, organization_id)
        day_start = datetime.combine(target_date, datetime.min.time(), tzinfo=zone)
        day_end = day_start + timedelta(days=1)

        for bd in blackouts:
            if bd.end_dt <= day_start or bd.start_dt >= day_end:
                continue
            overlap_start = max(bd.start_dt, day_start)
            overlap_end = min(bd.end_dt, day_end)
            slots = [s for s in slots if s >= overlap_end or s + timedelta(minutes=service.duration_minutes) <= overlap_start]

        occupied = await BookingRepo.get_confirmed_in_range(
            self.session, organization_id, day_start, day_end
        )
        occupied_times = {(b.start_dt, b.end_dt) for b in occupied}

        def overlaps(s: datetime, e: datetime) -> bool:
            for os, oe in occupied_times:
                if s < oe and e > os:
                    return True
            return False

        slot_end_delta = timedelta(minutes=service.duration_minutes)
        now = datetime.now(zone)
        result = [
            s
            for s in slots
            if s >= now and not overlaps(s, s + slot_end_delta)
        ]
        return sorted(result)

    async def create_booking(
        self,
        organization_id: int,
        service_id: int,
        client_user_id: int,
        slot_start: datetime,
        client_name: str,
        client_phone: Optional[str] = None,
    ) -> Optional[Booking]:
        sub = await SubscriptionRepo.get_by_org(self.session, organization_id)
        if not sub or sub.status != "ACTIVE":
            return None
        now_utc = datetime.now(ZoneInfo("UTC"))
        end = sub.current_period_end
        if end.tzinfo is None:
            end = end.replace(tzinfo=ZoneInfo("UTC"))
        if end < now_utc:
            return None

        service = await ServiceRepo.get_by_id(self.session, service_id)
        if not service or not service.is_active:
            return None

        slot_end = slot_start + timedelta(minutes=service.duration_minutes)
        try:
            return await BookingRepo.create(
                self.session,
                organization_id=organization_id,
                service_id=service_id,
                client_user_id=client_user_id,
                start_dt=slot_start,
                end_dt=slot_end,
                client_name=client_name,
                client_phone=client_phone,
            )
        except Exception:
            return None

    async def cancel_booking(self, booking_id: int, client_user_id: int) -> bool:
        booking = await BookingRepo.get_by_id(self.session, booking_id)
        if not booking or booking.client_user_id != client_user_id:
            return False
        if booking.status == BookingStatus.CANCELED.value:
            return False
        await BookingRepo.update_status(self.session, booking_id, BookingStatus.CANCELED.value)
        return True

    async def confirm_booking(self, booking_id: int, org_id: int, user_id: int) -> bool:
        from app.db.repo import OrganizationAdminRepo

        if not await OrganizationAdminRepo.is_admin(self.session, org_id, user_id):
            return False
        booking = await BookingRepo.get_by_id(self.session, booking_id)
        if not booking or booking.organization_id != org_id:
            return False
        if booking.status != BookingStatus.PENDING.value:
            return False
        await BookingRepo.update_status(self.session, booking_id, BookingStatus.CONFIRMED.value)
        return True

    async def reject_booking(self, booking_id: int, org_id: int, user_id: int) -> bool:
        from app.db.repo import OrganizationAdminRepo

        if not await OrganizationAdminRepo.is_admin(self.session, org_id, user_id):
            return False
        booking = await BookingRepo.get_by_id(self.session, booking_id)
        if not booking or booking.organization_id != org_id:
            return False
        if booking.status != BookingStatus.PENDING.value:
            return False
        await BookingRepo.update_status(self.session, booking_id, BookingStatus.CANCELED.value)
        return True
