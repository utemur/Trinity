"""Точка входа бота ЮрПомощник Узбекистан."""

import asyncio
import logging

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

from app.config import config
from app.handlers import about, disclaimer, help as help_handler, lang, privacy, qa, start, urgent
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
    dp.include_router(about.router)
    dp.include_router(qa.router)
    return dp


async def health(_: web.Request) -> web.Response:
    """Health check для Render."""
    return web.Response(text="ok")


async def on_webhook_startup(bot: Bot) -> None:
    url = f"{config.WEBHOOK_URL.rstrip('/')}{config.WEBHOOK_PATH}"
    await bot.set_webhook(url, secret_token=config.WEBHOOK_SECRET)
    logger.info("Webhook set: %s", url)


async def run_polling() -> None:
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = create_dp()
    logger.info("Bot starting (long polling)")
    await dp.start_polling(bot)


def run_webhook() -> None:
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = create_dp()
    dp.startup.register(on_webhook_startup)

    app = web.Application()
    app.router.add_get("/", health)
    webhook_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=config.WEBHOOK_SECRET,
    )
    webhook_handler.register(app, path=config.WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    logger.info("Bot starting (webhook) on port %s", config.PORT)
    web.run_app(app, host="0.0.0.0", port=config.PORT)


def main() -> None:
    config.validate()

    if config.use_webhook():
        run_webhook()  # блокирует до остановки
    else:
        asyncio.run(run_polling())


if __name__ == "__main__":
    main()
