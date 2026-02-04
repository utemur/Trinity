"""Обработчик /start."""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.i18n.texts import TEXTS
from app.keyboards.inline import LangCb, lang_keyboard
from app.keyboards.reply import main_menu

router = Router(name="start")

# In-memory: user_id -> lang. При рестарте сбросится.
_user_lang: dict[int, str] = {}


def get_lang(user_id: int) -> str:
    return _user_lang.get(user_id, "ru")


def set_lang(user_id: int, lang: str) -> None:
    _user_lang[user_id] = lang


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        TEXTS["ru"]["choose_lang"],
        reply_markup=lang_keyboard(),
    )


@router.callback_query(LangCb.filter())
async def on_lang_selected(cq: CallbackQuery, callback_data: LangCb, state: FSMContext) -> None:
    user_id = cq.from_user.id if cq.from_user else 0
    is_first = user_id not in _user_lang
    set_lang(user_id, callback_data.code)
    await state.clear()
    await cq.answer()

    lang = callback_data.code
    if is_first:
        welcome = TEXTS[lang]["welcome"]
        disclaimer = TEXTS[lang]["disclaimer"]
        msg = f"{welcome}\n\n{disclaimer}"
    else:
        msg = "Язык изменён на Русский ✓" if lang == "ru" else "Til o'zbekchaga o'zgartirildi ✓"

    await cq.message.edit_text(msg)
    await cq.message.answer("Меню:", reply_markup=main_menu())
