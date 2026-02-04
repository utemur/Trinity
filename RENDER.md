# Деплой на Render

## Важно: используйте Background Worker, не Web Service

Telegram-бот с long polling **не слушает порт**. Render Web Service требует открытый порт — используйте Background Worker.

### Шаги

1. **New** → **Background Worker**
2. Подключите репозиторий `utemur/Trinity`
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `python -m app`
5. **Environment**:
   - `BOT_TOKEN` — токен от @BotFather
   - `OPENAI_API_KEY` — ключ OpenAI
   - `OPENAI_MODEL` — gpt-4o-mini (по умолчанию)
   - `TZ` — Asia/Tashkent
