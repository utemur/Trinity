"""Настройка логирования. Только технические логи, без текста вопросов/ответов."""

import hashlib
import logging
import sys


def hash_user_id(user_id: int) -> str:
    """Хэш user_id для логов."""
    return hashlib.sha256(str(user_id).encode()).hexdigest()[:12]


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
