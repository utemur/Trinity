"""Скрипт для заполнения тестовыми данными."""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()


async def seed() -> None:
    from app.config import config
    from app.db.session import async_session_factory
    from app.db.repo import (
        AvailabilityRuleRepo,
        OrganizationAdminRepo,
        OrganizationRepo,
        ServiceRepo,
        SubscriptionRepo,
    )

    async with async_session_factory() as session:
        orgs = await OrganizationRepo.get_all(session)
        if orgs:
            print("Данные уже есть. Пропуск.")
            return

        org = await OrganizationRepo.create(session, name="Салон красоты «Стиль»", timezone="Asia/Tashkent")
        admin_ids = config.ADMIN_IDS
        if admin_ids:
            await OrganizationAdminRepo.add(session, org.id, admin_ids[0])

        await ServiceRepo.create(session, org.id, "Стрижка женская", 60, 1500)
        await ServiceRepo.create(session, org.id, "Маникюр", 45, 800)

        for wd in range(5):
            await AvailabilityRuleRepo.create(session, org.id, wd, "09:00", "18:00", 30)

        zone = ZoneInfo(org.timezone)
        now = datetime.now(zone)
        end = now + timedelta(days=30)
        await SubscriptionRepo.create_or_update(
            session, org.id, "BASIC", now, end, "ACTIVE"
        )

        await session.commit()
        print("Seed выполнен: 1 организация, 2 услуги, расписание пн–пт 09:00–18:00, подписка 30 дней.")


if __name__ == "__main__":
    asyncio.run(seed())
