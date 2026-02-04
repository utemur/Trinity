"""Inline-клавиатуры."""

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class LangCb(CallbackData, prefix="lang"):
    code: str


def lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data=LangCb(code="ru").pack()),
                InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data=LangCb(code="uz").pack()),
            ],
        ]
    )
