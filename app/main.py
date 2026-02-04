"""Точка входа бота ЮрПомощник Узбекистан."""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import config
from app.handlers import disclaimer, help as help_handler, lang, privacy, qa, start, urgent
from app.utils.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def create_dp() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(start.router)
    dp.include_router(lang.router)
    dp.include_router(help_handler.router)
    dp.include_router(disclaimer.router)
    dp.include_router(privacy.router)
    dp.include_router(urgent.router)
    dp.include_router(qa.router)
    return dp


async def main() -> None:
    config.validate()

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = create_dp()

    logger.info("Bot starting (long polling)")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
