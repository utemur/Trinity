"""Фильтр PII и правила эскалации к юристу."""

import re
from typing import Tuple

# Паттерны персональных данных (упрощённо)
PII_PATTERNS = [
    r"\b\d{2}\s?\d{2}\s?\d{6}\b",  # паспорт серия номер
    r"\b[AАВЕКМНОРСТУХ]\d{2}\s?\d{2}\s?\d{6}\b",  # паспорт РУз
    r"\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b",  # карта 16 цифр
    r"\b\d{3}\s?\d{3}\s?\d{3}\s?\d{3}\b",  # карта 12 цифр
    r"\b\d{9}\b",  # ИНН 9 цифр
    r"\b\d{14}\b",  # ИНН 14 цифр
    r"(?:улица|ул\.?|проспект|пр\.?|дом|д\.?|квартира|кв\.?)\s*[^\n,]+",
    r"(?:ko'cha|tuman|shahar|uy|kv)\s*[^\n,]+",
]

# Ключевые слова высокорисковых тем
HIGH_RISK_KEYWORDS = [
    "уголовн", "criminal", "jinoyat",
    "задержан", "qamalgan", "qamoq",
    "насилие", "zo'ravonlik",
    "угроз", "qo'rqitish",
    "суд", "sud", "иск", "da'vo",
    "депортац", "deportatsiya",
    "миграц", "migratsiya",
    "срок", "muddat",
    "арест", "hibsga",
    "следствен", "tergov",
]


def contains_pii(text: str) -> Tuple[bool, str]:
    """Проверяет наличие PII. Возвращает (найдено, описание)."""
    text_lower = text.lower().strip()
    for pattern in PII_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True, "Обнаружены возможные персональные данные"
    return False, ""


def is_high_risk(text: str) -> bool:
    """Проверяет, относится ли вопрос к высокорисковой теме."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in HIGH_RISK_KEYWORDS)
