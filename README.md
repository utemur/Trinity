# Trinity Bot

Минимальный Telegram-бот. Функционал добавляется пошагово.

## Запуск

```bash
cp .env.example .env
# Укажите BOT_TOKEN
pip install -r requirements.txt
python -m app
```

## Docker

```bash
docker compose up -d
```

## Render

Используйте **Background Worker**, не Web Service. См. [RENDER.md](RENDER.md).

## Текущий функционал

- `/start` — выбор языка (Русский / English)
