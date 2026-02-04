"""Обработчик дисклеймера."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.handlers.start import get_lang
from app.i18n.texts import TEXTS
from app.keyboards.reply import get_menu_texts

router = Router(name="disclaimer")


@router.message(Command("disclaimer"))
@router.message(lambda m: m.text and m.text in get_menu_texts()[2])
async def cmd_disclaimer(message: Message) -> None:
    lang = get_lang(message.from_user.id if message.from_user else 0)
    text = TEXTS[lang]["disclaimer"]
    extra = "\n\nМы не храним вопросы и ответы." if lang == "ru" else "\n\nBiz savol va javoblarni saqlamaymiz."
    await message.answer(text + extra)
