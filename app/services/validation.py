"""Валидация ввода пользователя."""

import re
from datetime import date, datetime
from typing import Optional

from zoneinfo import ZoneInfo


def validate_phone(phone: str) -> Optional[str]:
    digits = re.sub(r"\D", "", phone)
    if len(digits) >= 10:
        return digits
    return None


def validate_name(name: str) -> Optional[str]:
    cleaned = name.strip()
    if 2 <= len(cleaned) <= 100:
        return cleaned
    return None


def parse_date(text: str, tz: str = "Asia/Tashkent") -> Optional[date]:
    try:
        for fmt in ("%d.%m.%Y", "%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(text.strip(), fmt).date()
            except ValueError:
                continue
        return None
    except (ValueError, TypeError):
        return None


def parse_time(text: str) -> Optional[tuple[int, int]]:
    try:
        for fmt in ("%H:%M", "%H.%M"):
            try:
                dt = datetime.strptime(text.strip(), fmt)
                return dt.hour, dt.minute
            except ValueError:
                continue
        return None
    except (ValueError, TypeError):
        return None


def to_aware_datetime(d: date, hour: int, minute: int, tz: str) -> datetime:
    return datetime(d.year, d.month, d.day, hour, minute, 0, tzinfo=ZoneInfo(tz))
