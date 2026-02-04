"""Обработчик «О боте»."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.handlers.start import get_lang
from app.i18n.texts import TEXTS
from app.keyboards.reply import get_menu_texts

router = Router(name="about")


@router.message(Command("about"))
@router.message(lambda m: m.text and m.text in get_menu_texts()[4])
async def about_bot(message: Message) -> None:
    lang = get_lang(message.from_user.id if message.from_user else 0)
    await message.answer(TEXTS[lang]["about_bot"])
