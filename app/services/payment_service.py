"""Сервис оплаты подписки. MVP: ручная активация. TODO: Click, Payme."""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from zoneinfo import ZoneInfo

from app.db.models import Subscription
from app.db.repo import OrganizationRepo, SubscriptionRepo


class PaymentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def activate_plan_manual(
        self, organization_id: int, plan: str = "BASIC", days: int = 30
    ) -> Optional[Subscription]:
        org = await OrganizationRepo.get_by_id(self.session, organization_id)
        if not org:
            return None
        zone = ZoneInfo(org.timezone)
        now = datetime.now(zone)
        end = now + timedelta(days=days)
        return await SubscriptionRepo.create_or_update(
            self.session,
            organization_id=organization_id,
            plan=plan,
            period_start=now,
            period_end=end,
            status="ACTIVE",
        )

    async def get_subscription_status(self, organization_id: int) -> Optional[dict]:
        sub = await SubscriptionRepo.get_by_org(self.session, organization_id)
        if not sub:
            return None
        now = datetime.now(ZoneInfo("UTC"))
        end = sub.current_period_end
        if end.tzinfo is None:
            end = end.replace(tzinfo=ZoneInfo("UTC"))
        is_active = sub.status == "ACTIVE" and end > now
        return {
            "plan": sub.plan,
            "status": sub.status,
            "current_period_end": sub.current_period_end,
            "is_active": is_active,
        }

    # TODO: integrate Click / Payme
    # async def create_payment_link(self, organization_id: int, plan: str, amount: int) -> Optional[str]:
    #     pass
    # async def handle_webhook(self, payload: dict) -> bool:
    #     pass
