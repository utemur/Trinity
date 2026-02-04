"""Обработчик срочного случая."""

from aiogram import Router
from aiogram.types import Message

from app.handlers.start import get_lang
from app.i18n.texts import TEXTS
from app.keyboards.reply import URGENT

router = Router(name="urgent")


@router.message(lambda m: m.text == URGENT)
async def urgent_case(message: Message) -> None:
    lang = get_lang(message.from_user.id if message.from_user else 0)
    title = TEXTS[lang]["urgent_title"]
    text = TEXTS[lang]["urgent_text"]
    await message.answer(f"<b>{title}</b>\n\n{text}")
