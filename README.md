# Telegram-бот для бронирований

Универсальный бот для приёма бронирований (салоны, аренда, рестораны, мероприятия) с оплатой подписки.

## Стек

- Python 3.11+
- aiogram 3.x
- PostgreSQL (asyncpg + SQLAlchemy async)
- Alembic (миграции)
- APScheduler (напоминания)

## Быстрый старт

### 1. Docker Compose (рекомендуется)

```bash
cp .env.example .env
# Отредактируйте .env: BOT_TOKEN, ADMIN_IDS
docker compose up -d
```

Бот и PostgreSQL запустятся. iCal-сервер доступен на порту 8080.

### 2. Локально (без Docker)

```bash
# PostgreSQL должен быть запущен
cp .env.example .env
# Укажите DATABASE_URL, BOT_TOKEN, ADMIN_IDS
pip install -r requirements.txt
alembic upgrade head
python scripts/seed.py
python -m app
```

## Конфигурация (.env)

| Переменная   | Описание                          |
|-------------|-----------------------------------|
| BOT_TOKEN   | Токен бота от @BotFather          |
| DATABASE_URL| postgresql+asyncpg://user:pass@host:5432/db |
| ADMIN_IDS   | ID админов через запятую          |
| TIMEZONE    | Часовой пояс (по умолчанию Asia/Tashkent) |
| BASE_URL    | Для webhook (пока не используется) |
| ICAL_SERVER_PORT | Порт iCal-сервера (8080)    |

## Команды админа

| Команда | Описание |
|---------|----------|
| /admin | Админ-панель |
| /create_org Название | Создать организацию |
| /add_service org_id Название Длительность_мин [цена] | Добавить услугу |
| /add_rule org_id weekday start end [step] | Добавить правило расписания (weekday 0=Пн) |
| /add_blackout org_id start_date end_date [reason] | Добавить выходной |
| /activate_plan org_id [дней] [план] | Активировать подписку вручную |

## iCal экспорт

Ссылка для подписки на календарь:
```
http://<host>:8080/ical/<organization_id>/<ical_token>.ics
```

Токен хранится в поле `ical_token` организации.

## Структура проекта

```
app/
  main.py
  config.py
  db/
    session.py
    models.py
    repo.py
    migrations/
  handlers/
    start.py
    client_booking.py
    admin_booking.py
    subscription.py
  keyboards/
    reply.py
    inline.py
  services/
    booking_service.py
    calendar_service.py
    reminder_service.py
    payment_service.py
    validation.py
  middlewares/
  utils/
```
