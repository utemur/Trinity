"""Конфигурация из переменных окружения."""

import os
import re

from dotenv import load_dotenv

load_dotenv()

# Telegram: secret_token только A-Z, a-z, 0-9, _, -
_WEBHOOK_SECRET_ALLOWED = re.compile(r"^[A-Za-z0-9_-]{1,256}$")


def _get_webhook_secret() -> str | None:
    s = (os.getenv("WEBHOOK_SECRET") or "").strip()
    return s if s and _WEBHOOK_SECRET_ALLOWED.match(s) else None


def _resolve_webhook_url() -> str:
    url = os.getenv("WEBHOOK_URL", "") or os.getenv("RENDER_EXTERNAL_URL", "")
    if url:
        return url
    host = os.getenv("RENDER_EXTERNAL_HOSTNAME", "")
    if host:
        return f"https://{host}"
    # Fallback: Render Web Service — URL по имени сервиса
    name = os.getenv("RENDER_SERVICE_NAME", "")
    if name and os.getenv("RENDER") == "true":
        return f"https://{name}.onrender.com"
    return ""


class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    TZ: str = os.getenv("TZ", "Asia/Tashkent")

    # Webhook (для Render Web Service — устраняет TelegramConflictError)
    WEBHOOK_URL: str = _resolve_webhook_url()
    WEBHOOK_PATH: str = os.getenv("WEBHOOK_PATH", "/webhook")
    WEBHOOK_SECRET: str | None = _get_webhook_secret()
    PORT: int = int(os.getenv("PORT", "8080"))

    @classmethod
    def use_webhook(cls) -> bool:
        return bool(cls.WEBHOOK_URL)

    @classmethod
    def validate(cls) -> None:
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не задан в .env")
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY не задан в .env")
        if cls.use_webhook() and not cls.WEBHOOK_URL.startswith("https://"):
            raise ValueError("WEBHOOK_URL должен начинаться с https://")


config = Config()
