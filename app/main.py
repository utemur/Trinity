"""Точка входа бота."""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import config
from app.db.session import init_db
from app.handlers import admin_booking, client_booking, start, subscription
from app.middlewares.db import DbSessionMiddleware
from app.utils.ical_server import run_ical_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


async def send_reminder(bot: Bot, booking, reminder_type: str) -> None:
    svc_name = booking.service.name if booking.service else "—"
    msg = (
        f"⏰ Напоминание о бронировании #{booking.id}\n\n"
        f"Дата и время: {booking.start_dt.strftime('%d.%m.%Y %H:%M')}\n"
        f"Услуга: {svc_name}\n"
    )
    if reminder_type == "24h":
        msg = "За 24 часа:\n\n" + msg
    else:
        msg = "За 2 часа:\n\n" + msg

    try:
        await bot.send_message(booking.client_user_id, msg)
    except Exception as e:
        logger.warning("Reminder send failed for user %s: %s", booking.client_user_id, e)


async def reminder_job(bot: Bot) -> None:
    from app.db.session import async_session_factory
    from app.services.reminder_service import ReminderService

    async with async_session_factory() as session:
        rs = ReminderService(session)
        sent = await rs.process_due_reminders(
            lambda b, rtype: send_reminder(bot, b, rtype)
        )
        if sent:
            logger.info("Sent %d reminders", sent)


@asynccontextmanager
async def lifespan(app):
    yield
    pass


def create_dp() -> Dispatcher:
    dp = Dispatcher()
    dp.message.middleware(DbSessionMiddleware())
    dp.callback_query.middleware(DbSessionMiddleware())

    dp.include_router(start.router)
    dp.include_router(client_booking.router)
    dp.include_router(admin_booking.router)
    dp.include_router(subscription.router)

    return dp


async def main() -> None:
    config.validate()

    await init_db()

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = create_dp()

    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        lambda: asyncio.create_task(reminder_job(bot)),
        "interval",
        minutes=5,
    )
    scheduler.start()

    ical_task = asyncio.create_task(run_ical_server())

    logger.info("Bot starting (long polling)")
    try:
        await dp.start_polling(bot)
    finally:
        ical_task.cancel()
        try:
            await ical_task
        except asyncio.CancelledError:
            pass
        scheduler.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
