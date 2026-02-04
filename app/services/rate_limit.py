"""Rate limit: 1 запрос в 20 сек на пользователя + глобальный лимит параллельных."""

import asyncio
import time
from contextlib import asynccontextmanager
from typing import Dict

USER_COOLDOWN = 20
MAX_CONCURRENT = 5

_last_request: Dict[int, float] = {}
_concurrent = 0
_lock = asyncio.Lock()


async def check_user_limit(user_id: int) -> bool:
    """True если можно отправить запрос."""
    async with _lock:
        now = time.time()
        last = _last_request.get(user_id, 0)
        return (now - last) >= USER_COOLDOWN


@asynccontextmanager
async def acquire_slot(user_id: int):
    """Контекстный менеджер. Yields True если слот получен, иначе False."""
    global _concurrent
    async with _lock:
        now = time.time()
        last = _last_request.get(user_id, 0)
        if now - last < USER_COOLDOWN:
            yield False
            return
        if _concurrent >= MAX_CONCURRENT:
            yield False
            return
        _last_request[user_id] = now
        _concurrent += 1

    try:
        yield True
    finally:
        async with _lock:
            _concurrent = max(0, _concurrent - 1)
