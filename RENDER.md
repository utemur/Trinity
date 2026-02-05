# Деплой EmployerBot на Render

## Важно: Background Worker, не Web Service

EmployerBot использует **long polling** (Telegraf) — не слушает HTTP-порт. Render Web Service требует открытый порт и завершит деплой по таймауту. Используйте **Background Worker**.

---

## Пошаговая инструкция

### 1. PostgreSQL (если ещё нет)

1. В Render: **New** → **PostgreSQL**
2. Name: `trinity-db`, Region: Frankfurt
3. Создайте БД, скопируйте **Internal Database URL** (для сервисов в той же группе) или **External Database URL**

### 2. Background Worker

1. **New** → **Background Worker**
2. Подключите репозиторий `utemur/Trinity`
3. Ветка: `main`

### 3. Настройки сервиса

| Поле | Значение |
|------|----------|
| **Name** | `employer-bot` |
| **Region** | Frankfurt |
| **Branch** | `main` |
| **Build Command** | `corepack enable && pnpm install && pnpm db:generate && pnpm db:migrate && pnpm employer:build` |
| **Start Command** | `node apps/employer-bot/dist/index.js` |
| **Plan** | Free |

> Render поддерживает pnpm (через corepack). Если ошибка версии — добавьте в Environment: `COREPACK_ENABLE_STRICT=0`

### 4. Переменные окружения

В **Environment** добавьте:

| Key | Value |
|-----|-------|
| `BOT_TOKEN_EMPLOYER` | Токен от [@BotFather](https://t.me/BotFather) |
| `DATABASE_URL` | URL PostgreSQL (из шага 1) |
| `ADMIN_TELEGRAM_ID` | (опционально) Ваш Telegram ID для копий заявок |

**Если PostgreSQL на Render:** добавьте сервис БД в ту же **Environment Group** — переменная `DATABASE_URL` подтянется автоматически.

### 5. Миграции

Prisma миграции нужно выполнить один раз. Варианты:

**A) Через Render Shell (если есть):**
```bash
pnpm db:migrate
```

**B) Локально** — подключитесь к External Database URL и выполните:
```bash
DATABASE_URL="postgresql://..." pnpm db:migrate
```

**C) Добавить в Build Command** (миграции при каждом деплое):
```
pnpm install && pnpm db:generate && pnpm db:migrate && pnpm employer:build
```

### 6. Деплой

Нажмите **Create Background Worker**. Дождитесь сборки. В логах должно появиться: `EmployerBot started`.

### 7. Проверка

Откройте бота в Telegram и отправьте `/start`.

---

## Если у вас уже Web Service (старый Python-бот)

EmployerBot — это **новый** Node.js-бот. Long polling не работает в Web Service (нет порта → таймаут).

**Что сделать:**
1. Остановите или удалите старый Web Service
2. Создайте **Background Worker** по инструкции выше
3. Используйте тот же `BOT_TOKEN_EMPLOYER` (если это тот же бот) или создайте нового через @BotFather

---

## Ограничения Free-плана

- Сервис может «засыпать» после ~15 минут без активности
- Первый запрос после пробуждения — 30–60 секунд
- PostgreSQL Free — данные удаляются через 90 дней
