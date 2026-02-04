"""Обработчик вопросов и ответов."""

import logging

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from app.handlers.start import get_lang, set_lang
from app.i18n.texts import TEXTS
from app.keyboards.reply import ASK, main_menu
from app.services.openai_service import ask_openai
from app.services.rate_limit import acquire_slot, check_user_limit
from app.services.safety import contains_pii, is_high_risk
from app.utils.logging import hash_user_id

logger = logging.getLogger(__name__)
router = Router(name="qa")


class QAStates(StatesGroup):
    waiting_question = State()


@router.message(lambda m: m.text == ASK)
async def ask_question_start(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id if message.from_user else 0
    lang = get_lang(user_id)
    await state.set_state(QAStates.waiting_question)
    await message.answer(TEXTS[lang]["ask_question"])


@router.message(QAStates.waiting_question, lambda m: m.text)
async def process_question(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id if message.from_user else 0
    lang = get_lang(user_id)
    question = (message.text or "").strip()

    if not question:
        return

    # PII check
    has_pii, _ = contains_pii(question)
    if has_pii:
        await message.answer(TEXTS[lang]["pii_warning"])
        return

    # Rate limit
    if not await check_user_limit(user_id):
        await message.answer(TEXTS[lang]["rate_limit"])
        return

    async with acquire_slot(user_id) as acquired:
        if not acquired:
            await message.answer(TEXTS[lang]["rate_limit"])
            return

        await message.answer(TEXTS[lang]["processing"])
        logger.info("Question from user %s", hash_user_id(user_id))

        try:
            answer = await ask_openai(question, lang)
        except Exception as e:
            logger.warning("OpenAI error for user %s: %s", hash_user_id(user_id), e)
            answer = None

    await state.clear()

    if not answer:
        await message.answer(TEXTS[lang]["error_api"])
        return

    if is_high_risk(question):
        urgent_ru = "\n\n🆘 Срочно: обратитесь к аккредитованному юристу/адвокату в РУз."
        urgent_uz = "\n\n🆘 Shoshilinch: O'zbekiston Respublikasidagi akkreditatsiyalangan yurist/advokatga murojaat qiling."
        answer += urgent_ru if lang == "ru" else urgent_uz

    disclaimer = TEXTS[lang]["disclaimer"]
    full_answer = f"{answer}\n\n{disclaimer}"

    if len(full_answer) > 4000:
        full_answer = full_answer[:3997] + "..."

    await message.answer(full_answer, reply_markup=main_menu())
