"""Сервис OpenAI Responses API."""

import asyncio
import logging
from typing import Optional

from openai import OpenAI

from app.config import config

logger = logging.getLogger(__name__)

SYSTEM_RU = """Ты — справочный бот по законодательству Республики Узбекистан. 
Отвечай ТОЛЬКО справочно. НЕ давай точных вердиктов, НЕ обещай исход дела.
Используй формулировки: "обычно", "может зависеть", "возможный порядок действий".
НЕ проси паспорт, адрес, ИНН, номера карт.
При нехватке фактов — задавай уточняющие вопросы.
При высоких рисках (уголовное, задержание, суд, миграция) — рекомендуй обратиться к юристу.

Формат ответа (строго):
A) Краткий вывод (1–3 предложения)
B) Что уточнить (1–5 вопросов, если нужно)
C) Возможные шаги (буллеты)
D) Риски / когда нужен юрист (буллеты)
E) Дисклеймер: "За профессиональной помощью — к аккредитованному юристу в РУз."
"""

SYSTEM_UZ = """Sen — O'zbekiston Respublikasi qonunchiligi bo'yicha ma'lumotnoma boti.
Faqat ma'lumotnoma sifatida javob bering. Aniq hukm bermang, ish natijasini va'dalamang.
"Odatda", "bog'liq bo'lishi mumkin", "mumkin bo'lgan tartib" iboralaridan foydalaning.
Pasport, manzil, INN, karta raqamlarini so'ramang.
Faktlar yetarli bo'lmasa — aniqlovchi savollar bering.
Yuqori xavf (jinoyat, hibsga olish, sud, migratsiya) — yuristga murojaat qilishni tavsiya qiling.

Javob formati (qat'iy):
A) Qisqa xulosa (1–3 gap)
B) Nimalarni aniqlashtirish kerak (1–5 savol, kerak bo'lsa)
C) Mumkin bo'lgan qadamlar (ro'yxat)
D) Xavflar / qachon yurist kerak (ro'yxat)
E) Ogohlantirish: "Professional yordam uchun — O'zbekiston Respublikasidagi akkreditatsiyalangan yuristga."
"""


def _get_instructions(lang: str) -> str:
    return SYSTEM_UZ if lang == "uz" else SYSTEM_RU


def _extract_text(response) -> str:
    """Извлекает текст из ответа Responses API."""
    if hasattr(response, "output_text") and response.output_text:
        return response.output_text
    if not getattr(response, "output", None):
        return ""
    text_parts = []
    for item in response.output:
        if hasattr(item, "content") and item.content:
            for c in item.content:
                if hasattr(c, "text") and c.text:
                    text_parts.append(c.text)
    return "\n".join(text_parts)


def _ask_responses_api(client: OpenAI, question: str, instructions: str) -> Optional[str]:
    """Responses API."""
    response = client.responses.create(
        model=config.OPENAI_MODEL,
        instructions=instructions,
        input=question,
        max_output_tokens=900,
        store=False,
    )
    return _extract_text(response)


def _ask_chat_api(client: OpenAI, question: str, instructions: str) -> Optional[str]:
    """Fallback: Chat Completions API."""
    response = client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": question},
        ],
        max_tokens=900,
    )
    if response.choices:
        return response.choices[0].message.content
    return None


async def ask_openai(question: str, lang: str) -> Optional[str]:
    """Отправляет вопрос в OpenAI. Retry с backoff. Возвращает текст или None."""
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    instructions = _get_instructions(lang)

    use_responses = hasattr(client, "responses")

    for attempt in range(3):
        try:
            if use_responses:
                result = await asyncio.to_thread(
                    _ask_responses_api, client, question, instructions
                )
            else:
                result = await asyncio.to_thread(
                    _ask_chat_api, client, question, instructions
                )
            return result
        except Exception as e:
            wait = 2 ** attempt
            logger.warning("OpenAI attempt %s failed: %s, retry in %ss", attempt + 1, e, wait)
            await asyncio.sleep(wait)

    return None
