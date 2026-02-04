"""Reply-клавиатура (постоянное меню)."""

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from app.i18n.texts import TEXTS


def main_menu(lang: str = "ru") -> ReplyKeyboardMarkup:
    t = TEXTS.get(lang, TEXTS["ru"])
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t["menu_ask"])],
            [KeyboardButton(text=t["menu_lang"]), KeyboardButton(text=t["menu_disclaimer"])],
            [KeyboardButton(text=t["menu_urgent"])],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )


def get_menu_texts() -> tuple[str, str, str, str]:
    """Возвращает (ask, lang, disclaimer, urgent) для обоих языков — для матчинга в хендлерах."""
    ru = TEXTS["ru"]
    uz = TEXTS["uz"]
    return (
        (ru["menu_ask"], uz["menu_ask"]),
        (ru["menu_lang"], uz["menu_lang"]),
        (ru["menu_disclaimer"], uz["menu_disclaimer"]),
        (ru["menu_urgent"], uz["menu_urgent"]),
    )
