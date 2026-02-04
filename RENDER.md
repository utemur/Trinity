# Деплой на Render

## Важно: Background Worker, не Web Service

Telegram-бот с long polling **не слушает порт**. Render Web Service требует открытый порт и завершит деплой по таймауту. Используйте **Background Worker**.

---

## Пошаговая инструкция

### 1. Войти в Render

Перейдите на [render.com](https://render.com) и войдите (через GitHub удобнее).

### 2. Создать Background Worker

1. Нажмите **New** → **Background Worker**
2. В разделе **Connect a repository** выберите `utemur/Trinity` (или подключите GitHub, если репозиторий ещё не добавлен)
3. Убедитесь, что выбран правильный репозиторий и ветка `main`

### 3. Настройки сервиса

| Поле | Значение |
|------|----------|
| **Name** | `trinity-bot` (или любое) |
| **Region** | Frankfurt (или ближайший) |
| **Branch** | `main` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python -m app` |
| **Plan** | Free |

### 4. Переменные окружения

В разделе **Environment** добавьте:

| Key | Value |
|-----|-------|
| `BOT_TOKEN` | Токен от [@BotFather](https://t.me/BotFather) |
| `OPENAI_API_KEY` | Ключ API с [platform.openai.com](https://platform.openai.com) |
| `OPENAI_MODEL` | `gpt-4o-mini` (по умолчанию) |
| `TZ` | `Asia/Tashkent` |

### 5. Деплой

1. Нажмите **Create Background Worker**
2. Дождитесь сборки (2–5 минут)
3. В логах должно появиться: `Bot starting (long polling)`

### 6. Проверка

Откройте бота в Telegram и отправьте `/start`.

---

## Ограничения Free-плана

- Сервис может «засыпать» после ~15 минут без активности
- Первый запрос после пробуждения может занимать 30–60 секунд
