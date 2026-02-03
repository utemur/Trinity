"""Обработчик /start и выбор языка."""

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.keyboards.inline import lang_keyboard

router = Router(name="start")

TEXTS = {
    "ru": {
        "choose_lang": "Выберите язык / Choose language:",
        "welcome": "Добро пожаловать!",
    },
    "en": {
        "choose_lang": "Choose language / Выберите язык:",
        "welcome": "Welcome!",
    },
}


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        TEXTS["ru"]["choose_lang"],
        reply_markup=lang_keyboard(),
    )


@router.callback_query(lambda c: c.data and c.data.startswith("lang:"))
async def on_lang_selected(cq: CallbackQuery, state: FSMContext) -> None:
    lang = cq.data.split(":")[1]
    await state.update_data(lang=lang)
    await cq.answer()

    text = TEXTS[lang]["welcome"]
    await cq.message.edit_text(text)
