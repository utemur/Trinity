# Деплой на Render

## Важно: используйте Background Worker, не Web Service

Telegram-бот с long polling **не слушает порт** — он сам опрашивает Telegram API. Render Web Service требует открытый порт и завершает деплой по таймауту.

### Шаги

1. В Render нажмите **New** → **Background Worker** (не Web Service).
2. Подключите репозиторий `utemur/Trinity`.
3. Настройки:
   - **Name**: `trinity-bot`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python -m app`
4. В **Environment** добавьте:
   - `BOT_TOKEN` — токен от @BotFather
5. **Create Background Worker**.

Background Worker не проверяет порты и просто выполняет команду — подходит для long polling бота.
