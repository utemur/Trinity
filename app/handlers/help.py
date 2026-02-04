"""Обработчик /help."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.handlers.start import get_lang
from app.i18n.texts import TEXTS

router = Router(name="help")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    lang = get_lang(message.from_user.id if message.from_user else 0)
    await message.answer(TEXTS[lang]["help"])
