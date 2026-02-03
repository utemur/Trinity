"""Reply-клавиатуры (постоянное меню)."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BOOK = "📅 Забронировать"
MY_BOOKINGS = "🗓 Мои бронирования"
CANCEL_BOOKING = "❌ Отменить бронирование"
SETTINGS = "⚙️ Настройки"
SUBSCRIPTION = "💳 Подписка"


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BOOK), KeyboardButton(text=MY_BOOKINGS)],
            [KeyboardButton(text=CANCEL_BOOKING)],
            [KeyboardButton(text=SETTINGS), KeyboardButton(text=SUBSCRIPTION)],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )
