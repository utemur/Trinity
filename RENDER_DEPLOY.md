# Развёртывание бота на Render

## Пошаговая инструкция

### Шаг 1: Подготовка репозитория

Убедитесь, что проект запушен в GitHub (например, https://github.com/utemur/Trinity).

---

### Шаг 2: Создание аккаунта и проекта

1. Перейдите на [render.com](https://render.com) и войдите (через GitHub удобнее).
2. Нажмите **New** → **PostgreSQL**.
3. Заполните:
   - **Name**: `trinity-db`
   - **Database**: `booking_bot`
   - **User**: `trinity`
   - **Region**: выберите ближайший (например, Frankfurt)
   - **Plan**: Free
4. Нажмите **Create Database**.
5. Дождитесь создания. В разделе **Info** скопируйте **Internal Database URL** (формат `postgresql://...`).

---

### Шаг 3: Создание Web Service для бота

1. Нажмите **New** → **Web Service**.
2. Подключите репозиторий GitHub:
   - **Connect a repository** → выберите `utemur/Trinity` (или ваш форк).
   - Если репозитория нет — нажмите **Configure account** и дайте доступ.
3. Настройки сервиса:
   - **Name**: `trinity-bot`
   - **Region**: тот же, что у базы (например, Frankfurt)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && alembic upgrade head
     ```
   - **Start Command**:
     ```bash
     python -m app
     ```
   - **Plan**: Free

---

### Шаг 4: Переменные окружения

В разделе **Environment** добавьте:

| Key | Value |
|-----|-------|
| `BOT_TOKEN` | Токен бота от [@BotFather](https://t.me/BotFather) |
| `ADMIN_IDS` | Ваш Telegram ID (узнать: [@userinfobot](https://t.me/userinfobot)), через запятую для нескольких |
| `DATABASE_URL` | Вставьте **Internal Database URL** из шага 2 |
| `TIMEZONE` | `Asia/Tashkent` (или ваш часовой пояс) |
| `BASE_URL` | URL вашего сервиса, например `https://trinity-bot.onrender.com` |

**Важно:** если Render подставляет `DATABASE_URL` в формате `postgresql://`, приложение автоматически преобразует его в `postgresql+asyncpg://`.

---

### Шаг 5: Подключение базы данных

1. В настройках Web Service откройте **Environment**.
2. Нажмите **Add Environment Variable**.
3. Выберите **Add from Render** → **Database** → `trinity-db`.
4. Выберите переменную **Internal Database URL** и сохраните как `DATABASE_URL`.

Либо вручную скопируйте Internal Database URL из панели PostgreSQL и вставьте в `DATABASE_URL`.

---

### Шаг 6: Первый деплой

1. Нажмите **Create Web Service**.
2. Дождитесь сборки и запуска (обычно 2–5 минут).
3. В логах должны появиться строки:
   ```
   Bot starting (long polling)
   iCal server listening on port 10000
   ```

---

### Шаг 7: Seed-данные (первый запуск)

1. В панели сервиса откройте **Shell** (если доступен).
2. Выполните:
   ```bash
   python scripts/seed.py
   ```

Если Shell недоступен — подключитесь к базе локально с помощью **External Database URL** и выполните seed вручную, либо добавьте вызов seed в `buildCommand` (только для первого деплоя).

---

### Шаг 8: Проверка

1. Откройте бота в Telegram и отправьте `/start`.
2. Проверьте iCal: `https://<ваш-сервис>.onrender.com/health` — должен вернуть `{"status":"ok"}`.
3. Ссылка на календарь: `https://<ваш-сервис>.onrender.com/ical/{org_id}/{token}.ics` (после `/ical_link` в боте).

---

## Альтернатива: Blueprint (один клик)

1. В Render нажмите **New** → **Blueprint**.
2. Укажите репозиторий `utemur/Trinity`.
3. Файл `render.yaml` создаст PostgreSQL и Web Service.
4. В Environment добавьте `BOT_TOKEN` и `ADMIN_IDS`.
5. Запустите деплой.

---

## Ограничения Free-плана

- Сервис «засыпает» после ~15 минут без запросов; первый запрос может занимать 30–60 секунд.
- PostgreSQL Free — до 1 ГБ, данные хранятся 90 дней.
- Для стабильной работы без «засыпания» нужен платный план.

---

## Полезные ссылки

- [Render Docs](https://render.com/docs)
- [Render PostgreSQL](https://render.com/docs/databases)
