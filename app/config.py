"""Конфигурация из переменных окружения."""

import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    TZ: str = os.getenv("TZ", "Asia/Tashkent")

    @classmethod
    def validate(cls) -> None:
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не задан в .env")
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY не задан в .env")


config = Config()
