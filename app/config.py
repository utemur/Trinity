"""Конфигурация приложения из переменных окружения."""

import os
from typing import List

from dotenv import load_dotenv

load_dotenv()


def _parse_admin_ids(value: str) -> List[int]:
    if not value:
        return []
    return [int(x.strip()) for x in value.split(",") if x.strip().isdigit()]


class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/booking_bot"
    )
    ADMIN_IDS: List[int] = _parse_admin_ids(os.getenv("ADMIN_IDS", ""))
    TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Tashkent")
    BASE_URL: str = os.getenv("BASE_URL", "")
    ICAL_SERVER_PORT: int = int(os.getenv("ICAL_SERVER_PORT", "8080"))

    @classmethod
    def validate(cls) -> None:
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не задан в .env")


config = Config()
