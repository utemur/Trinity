# Деплой на Render

## Рекомендуется: Web Service с webhook

Используйте **Web Service** с webhook — это устраняет ошибку `TelegramConflictError` (конфликт нескольких экземпляров getUpdates). Telegram отправляет обновления на ваш URL, конфликтов нет.

---

## Вариант A: Web Service (рекомендуется)

### 1. Создать Web Service

1. **New** → **Web Service**
2. Подключите репозиторий `utemur/Trinity` (или свой)
3. Ветка `main`

### 2. Настройки

| Поле | Значение |
|------|----------|
| **Name** | `trinity-bot` |
| **Region** | Frankfurt |
| **Branch** | `main` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python -m app` |
| **Plan** | Free |

### 3. Переменные окружения

| Key | Value |
|-----|-------|
| `BOT_TOKEN` | Токен от [@BotFather](https://t.me/BotFather) |
| `OPENAI_API_KEY` | Ключ с [platform.openai.com](https://platform.openai.com) |
| `OPENAI_MODEL` | `gpt-4o-mini` |
| `TZ` | `Asia/Tashkent` |
| `WEBHOOK_SECRET` | Строка из букв, цифр, `_` и `-` (например, `mySecretToken123` или `openssl rand -hex 32`) |

**Важно:** Render задаёт `RENDER_EXTERNAL_URL` или `RENDER_SERVICE_NAME` — бот сам переключится на webhook. Если webhook не сработал, добавьте вручную `WEBHOOK_URL=https://ваш-сервис.onrender.com` (URL виден в дашборде Render).

### 4. Деплой

После деплоя в логах: `Bot starting (webhook) on port 10000`.

### 5. Проверка

Откройте бота в Telegram и отправьте `/start`.

---

## Вариант B: Background Worker (long polling)

Если нужен long polling (без webhook):

1. **New** → **Background Worker**
2. Те же настройки, но **не задавайте** `WEBHOOK_URL` и `RENDER_EXTERNAL_URL`
3. Убедитесь, что бот **нигде больше не запущен** (локально, другой хостинг) — иначе будет `TelegramConflictError`

---

## Ограничения Free-плана

- Сервис может «засыпать» после ~15 минут без активности
- Первый запрос после пробуждения может занимать 30–60 секунд
