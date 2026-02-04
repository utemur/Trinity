"""Reply-клавиатура (постоянное меню)."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

ASK = "❓ Задать вопрос"
LANG = "🌐 Язык"
DISCLAIMER = "ℹ️ Дисклеймер"
URGENT = "🆘 Срочный случай"


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=ASK)],
            [KeyboardButton(text=LANG), KeyboardButton(text=DISCLAIMER)],
            [KeyboardButton(text=URGENT)],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )
