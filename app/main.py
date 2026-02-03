"""Точка входа бота."""

import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import config
from app.handlers import start

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def create_dp() -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(start.router)
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
