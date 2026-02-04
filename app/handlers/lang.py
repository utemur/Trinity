"""Обработчик смены языка."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.handlers.start import get_lang
from app.i18n.texts import TEXTS
from app.keyboards.inline import lang_keyboard
from app.keyboards.reply import LANG

router = Router(name="lang")


@router.message(Command("lang"))
@router.message(lambda m: m.text == LANG)
async def cmd_lang(message: Message) -> None:
    lang = get_lang(message.from_user.id if message.from_user else 0)
    await message.answer(
        TEXTS[lang]["choose_lang"],
        reply_markup=lang_keyboard(),
    )
