"""Репозитории для работы с БД."""

from datetime import datetime
from typing import Optional, Sequence
from uuid import uuid4

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    AvailabilityRule,
    BlackoutDate,
    Booking,
    BookingStatus,
    Organization,
    OrganizationAdmin,
    ScheduledReminder,
    Service,
    Subscription,
    SubscriptionStatus,
)


class OrganizationRepo:
    @staticmethod
    async def get_by_id(session: AsyncSession, org_id: int) -> Optional[Organization]:
        result = await session.execute(select(Organization).where(Organization.id == org_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(session: AsyncSession) -> Sequence[Organization]:
        result = await session.execute(select(Organization).order_by(Organization.name))
        return result.scalars().all()

    @staticmethod
    async def create(session: AsyncSession, name: str, timezone: str = "Asia/Tashkent") -> Organization:
        org = Organization(name=name, timezone=timezone, ical_token=str(uuid4()).replace("-", ""))
        session.add(org)
        await session.flush()
        return org

    @staticmethod
    async def get_by_ical_token(session: AsyncSession, token: str) -> Optional[Organization]:
        result = await session.execute(select(Organization).where(Organization.ical_token == token))
        return result.scalar_one_or_none()


class OrganizationAdminRepo:
    @staticmethod
    async def add(session: AsyncSession, organization_id: int, user_id: int, role: str = "admin") -> OrganizationAdmin:
        admin = OrganizationAdmin(organization_id=organization_id, user_id=user_id, role=role)
        session.add(admin)
        await session.flush()
        return admin

    @staticmethod
    async def is_admin(session: AsyncSession, organization_id: int, user_id: int) -> bool:
        result = await session.execute(
            select(OrganizationAdmin).where(
                OrganizationAdmin.organization_id == organization_id,
                OrganizationAdmin.user_id == user_id,
            )
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def get_org_ids_for_user(session: AsyncSession, user_id: int) -> list[int]:
        result = await session.execute(
            select(OrganizationAdmin.organization_id).where(OrganizationAdmin.user_id == user_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_admins(session: AsyncSession, organization_id: int) -> Sequence[OrganizationAdmin]:
        result = await session.execute(
            select(OrganizationAdmin).where(OrganizationAdmin.organization_id == organization_id)
        )
        return result.scalars().all()


class ServiceRepo:
    @staticmethod
    async def get_by_org(session: AsyncSession, organization_id: int, active_only: bool = True) -> Sequence[Service]:
        q = select(Service).where(Service.organization_id == organization_id)
        if active_only:
            q = q.where(Service.is_active == True)
        q = q.order_by(Service.name)
        result = await session.execute(q)
        return result.scalars().all()

    @staticmethod
    async def get_by_id(session: AsyncSession, service_id: int) -> Optional[Service]:
        result = await session.execute(select(Service).where(Service.id == service_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        session: AsyncSession,
        organization_id: int,
        name: str,
        duration_minutes: int,
        price: Optional[int] = None,
    ) -> Service:
        svc = Service(
            organization_id=organization_id,
            name=name,
            duration_minutes=duration_minutes,
            price=price,
        )
        session.add(svc)
        await session.flush()
        return svc

    @staticmethod
    async def toggle_active(session: AsyncSession, service_id: int, is_active: bool) -> None:
        await session.execute(update(Service).where(Service.id == service_id).values(is_active=is_active))


class AvailabilityRuleRepo:
    @staticmethod
    async def get_by_org(session: AsyncSession, organization_id: int) -> Sequence[AvailabilityRule]:
        result = await session.execute(
            select(AvailabilityRule).where(AvailabilityRule.organization_id == organization_id)
        )
        return result.scalars().all()

    @staticmethod
    async def create(
        session: AsyncSession,
        organization_id: int,
        weekday: int,
        start_time: str,
        end_time: str,
        slot_step_minutes: int = 30,
    ) -> AvailabilityRule:
        from datetime import time as dt_time

        start_t = datetime.strptime(start_time, "%H:%M").time()
        end_t = datetime.strptime(end_time, "%H:%M").time()
        rule = AvailabilityRule(
            organization_id=organization_id,
            weekday=weekday,
            start_time=start_t,
            end_time=end_t,
            slot_step_minutes=slot_step_minutes,
        )
        session.add(rule)
        await session.flush()
        return rule

    @staticmethod
    async def delete_by_id(session: AsyncSession, rule_id: int) -> None:
        result = await session.execute(select(AvailabilityRule).where(AvailabilityRule.id == rule_id))
        rule = result.scalar_one_or_none()
        if rule:
            await session.delete(rule)


class BlackoutDateRepo:
    @staticmethod
    async def get_by_org(session: AsyncSession, organization_id: int) -> Sequence[BlackoutDate]:
        result = await session.execute(
            select(BlackoutDate).where(BlackoutDate.organization_id == organization_id)
        )
        return result.scalars().all()

    @staticmethod
    async def create(
        session: AsyncSession,
        organization_id: int,
        start_dt: datetime,
        end_dt: datetime,
        reason: Optional[str] = None,
    ) -> BlackoutDate:
        bd = BlackoutDate(
            organization_id=organization_id,
            start_dt=start_dt,
            end_dt=end_dt,
            reason=reason,
        )
        session.add(bd)
        await session.flush()
        return bd

    @staticmethod
    async def delete_by_id(session: AsyncSession, blackout_id: int) -> None:
        result = await session.execute(select(BlackoutDate).where(BlackoutDate.id == blackout_id))
        bd = result.scalar_one_or_none()
        if bd:
            await session.delete(bd)


class BookingRepo:
    @staticmethod
    async def create(
        session: AsyncSession,
        organization_id: int,
        service_id: int,
        client_user_id: int,
        start_dt: datetime,
        end_dt: datetime,
        client_name: str,
        client_phone: Optional[str] = None,
    ) -> Booking:
        booking = Booking(
            organization_id=organization_id,
            service_id=service_id,
            client_user_id=client_user_id,
            start_dt=start_dt,
            end_dt=end_dt,
            status=BookingStatus.PENDING.value,
            client_name=client_name,
            client_phone=client_phone,
        )
        session.add(booking)
        await session.flush()
        return booking

    @staticmethod
    async def get_by_id(session: AsyncSession, booking_id: int) -> Optional[Booking]:
        result = await session.execute(select(Booking).where(Booking.id == booking_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_future_by_client(session: AsyncSession, client_user_id: int) -> Sequence[Booking]:
        result = await session.execute(
            select(Booking)
            .where(
                Booking.client_user_id == client_user_id,
                Booking.start_dt >= datetime.utcnow(),
                Booking.status.in_([BookingStatus.PENDING.value, BookingStatus.CONFIRMED.value]),
            )
            .order_by(Booking.start_dt)
        )
        return result.scalars().all()

    @staticmethod
    async def get_pending_by_org(session: AsyncSession, organization_id: int) -> Sequence[Booking]:
        result = await session.execute(
            select(Booking)
            .where(
                Booking.organization_id == organization_id,
                Booking.status == BookingStatus.PENDING.value,
                Booking.start_dt >= datetime.utcnow(),
            )
            .order_by(Booking.start_dt)
        )
        return result.scalars().all()

    @staticmethod
    async def get_confirmed_in_range(
        session: AsyncSession, organization_id: int, start: datetime, end: datetime
    ) -> Sequence[Booking]:
        result = await session.execute(
            select(Booking).where(
                Booking.organization_id == organization_id,
                Booking.status.in_([BookingStatus.CONFIRMED.value, BookingStatus.PENDING.value]),
                Booking.start_dt < end,
                Booking.end_dt > start,
            )
        )
        return result.scalars().all()

    @staticmethod
    async def get_confirmed_future(session: AsyncSession) -> Sequence[Booking]:
        result = await session.execute(
            select(Booking).where(
                Booking.status == BookingStatus.CONFIRMED.value,
                Booking.start_dt >= datetime.utcnow(),
            )
        )
        return result.scalars().all()

    @staticmethod
    async def update_status(session: AsyncSession, booking_id: int, status: str) -> None:
        await session.execute(update(Booking).where(Booking.id == booking_id).values(status=status))

    @staticmethod
    async def get_stats(
        session: AsyncSession, organization_id: int, days: int = 7
    ) -> dict[str, int]:
        from datetime import timedelta

        since = datetime.utcnow() - timedelta(days=days)
        result = await session.execute(
            select(Booking.status, Booking.id)
            .where(
                Booking.organization_id == organization_id,
                Booking.created_at >= since,
            )
        )
        rows = result.all()
        stats = {"total": len(rows), "confirmed": 0, "canceled": 0, "pending": 0}
        for status, _ in rows:
            if status == BookingStatus.CONFIRMED.value:
                stats["confirmed"] += 1
            elif status == BookingStatus.CANCELED.value:
                stats["canceled"] += 1
            else:
                stats["pending"] += 1
        return stats


class SubscriptionRepo:
    @staticmethod
    async def get_by_org(session: AsyncSession, organization_id: int) -> Optional[Subscription]:
        result = await session.execute(
            select(Subscription).where(Subscription.organization_id == organization_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def create_or_update(
        session: AsyncSession,
        organization_id: int,
        plan: str,
        period_start: datetime,
        period_end: datetime,
        status: str = SubscriptionStatus.ACTIVE.value,
    ) -> Subscription:
        sub = await SubscriptionRepo.get_by_org(session, organization_id)
        if sub:
            sub.plan = plan
            sub.status = status
            sub.current_period_start = period_start
            sub.current_period_end = period_end
            await session.flush()
            return sub
        sub = Subscription(
            organization_id=organization_id,
            plan=plan,
            status=status,
            current_period_start=period_start,
            current_period_end=period_end,
        )
        session.add(sub)
        await session.flush()
        return sub


class ScheduledReminderRepo:
    @staticmethod
    async def create(
        session: AsyncSession, booking_id: int, remind_at: datetime, reminder_type: str
    ) -> ScheduledReminder:
        rem = ScheduledReminder(booking_id=booking_id, remind_at=remind_at, reminder_type=reminder_type)
        session.add(rem)
        await session.flush()
        return rem

    @staticmethod
    async def get_pending(session: AsyncSession) -> Sequence[ScheduledReminder]:
        result = await session.execute(
            select(ScheduledReminder).where(
                ScheduledReminder.sent == False,
                ScheduledReminder.remind_at <= datetime.utcnow(),
            )
        )
        return result.scalars().all()

    @staticmethod
    async def mark_sent(session: AsyncSession, reminder_id: int) -> None:
        await session.execute(
            update(ScheduledReminder).where(ScheduledReminder.id == reminder_id).values(sent=True)
        )
