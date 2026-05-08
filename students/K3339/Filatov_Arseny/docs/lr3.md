# Лабораторная работа 3 — Docker, интеграция парсера и очереди

## Цель

Упаковать Ledger (ЛР1) и парсер (логика ЛР2) в контейнеры, вызывать парсер по HTTP из FastAPI и (на максимальный балл) ставить парсинг в фон через **Celery** и **Redis**.

Код и артефакты: каталог **`Lr3/`** в репозитории (`students/K3339/Filatov_Arseny/Lr3/`), рядом с **`Lr1/`**, **`Lr2/`** и папкой **`docs/`**.

---

## Подзадача 1 — Docker

### Сервисы (`Lr3/docker-compose.yml`)

| Сервис | Образ / сборка | Назначение |
|--------|----------------|------------|
| `db` | `postgres:16-alpine` | Общая БД Ledger + таблица результатов парсинга |
| `redis` | `redis:7-alpine` | Брокер и backend результатов Celery |
| `parser` | Контекст `parser_service/`, файл `Dockerfile` | Микросервис FastAPI: загрузка HTML, извлечение `<title>`, `INSERT` в `lr2_parsed_web_title` |
| `api` | Контекст `Lr1/practice_1_3`, файл `Dockerfile` | Основное приложение: миграции Alembic при старте, `uvicorn` |
| `celery-worker` | тот же образ, что и `api` | `celery -A app.bootstrap_celery:celery_app worker` |

Сеть и зависимости задаются в Compose: API и воркер знают `PARSER_SERVICE_URL=http://parser:8100`, Redis — по имени сервиса `redis`, БД — `db`.

### Микросервис парсера

- Путь: `Lr3/parser_service/`
- Эндпоинты: `GET /health`, `POST /parse` (тело `{"url": "<https URL>"}`), дополнительно `POST /parse-raw-url?url=...` для примера из методички.
- Таблица **`lr2_parsed_web_title`** совпадает с ЛР2; создаётся через `SQLModel.metadata.create_all` при старте.

### Dockerfile API

`Lr1/practice_1_3/Dockerfile`: базовый `python:3.12-slim`, зависимости из того же каталога `requirements.txt`, команда по умолчанию — `alembic upgrade head` и запуск `uvicorn`. Образ переиспользуется сервисом `celery-worker` с другим `command`.

---

## Подзадача 2 — вызов парсера из Ledger

Роутер интеграции — файл **`parser_integration.py`** в дереве приложения Ledger: `students/K3339/Filatov_Arseny/Lr1/practice_1_3/app/api/routers/parser_integration.py`:

| Метод | Путь | Поведение |
|-------|------|-----------|
| `POST` | `/integrations/parser/sync` | Проксирует JSON в микросервис `POST /parse`, возвращает ответ парсера клиенту |

Используется **httpx**; базовый URL берётся из **`PARSER_SERVICE_URL`** (`app/core/config.py`).

---

## Подзадача 3 — Celery + Redis

| Компонент | Файл |
|-----------|------|
| Конфигурация Celery | `app/celery_app.py` |
| Регистрация задач при старте воркера | `app/bootstrap_celery.py` (импортирует `app.tasks.parse_tasks`) |
| Задача | `fetch_page_title` в `app/tasks/parse_tasks.py` — HTTP `POST` на парсер из фона |
| Брокер / backend | переменные `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND` |

Эндпоинты того же роутера:

| Метод | Путь | Поведение |
|-------|------|-----------|
| `POST` | `/integrations/parser/async` | `fetch_page_title.delay(url)` → ответ `{"task_id", "status": "queued"}` |
| `GET` | `/integrations/parser/async/{task_id}` | Состояние задачи; при успехе поле `result` с JSON парсера |

---

## Пример запуска

```bash
cd Lr3
docker compose up --build
```

Далее в Swagger Ledger (`/docs`): вызвать `/integrations/parser/sync` и `/integrations/parser/async`, для async — опросить `/integrations/parser/async/{task_id}`.
