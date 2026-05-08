# Лабораторная работа 3 — Docker, HTTP-парсер, Celery

## Состав

| Компонент | Расположение |
|-----------|--------------|
| **Docker Compose** | `docker-compose.yml` — PostgreSQL, Redis, Ledger API, микросервис парсера, Celery worker |
| **Dockerfile API** | `docker/api.Dockerfile` (контекст — `Lr1/practice_1_3`) |
| **Dockerfile парсера** | `docker/parser.Dockerfile` (контекст — `parser_service/`) |
| **Микросервис парсера** | `parser_service/` — FastAPI, `POST /parse`, запись в `lr2_parsed_web_title` |
| **Интеграция в Ledger** | `Lr1/practice_1_3/app/api/routers/parser_integration.py`, Celery в `app/celery_app.py`, задачи в `app/tasks/parse_tasks.py`, вход воркера `app/bootstrap_celery.py` |

## Быстрый старт

Из каталога `Lr3`:

```bash
docker compose up --build
```

После старта:

- Ledger API: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Парсер: [http://127.0.0.1:8100/docs](http://127.0.0.1:8100/docs)
- Redis: `localhost:6379`
- PostgreSQL: `localhost:5432`, пользователь `ledger`, пароль `ledger`, БД `ledger`

## Проверка сценариев ЛР3

1. **Синхронный вызов парсера из Ledger** (подзадача 2):

   `POST /integrations/parser/sync`  
   Тело JSON: `{"url": "https://example.com"}`

2. **Асинхронно через очередь** (подзадача 3):

   `POST /integrations/parser/async` с тем же телом — в ответе `task_id`.  
   Затем `GET /integrations/parser/async/{task_id}` — состояние и `result` после `SUCCESS`.

3. **Прямой вызов парсера** (подзадача 1):

   `POST http://127.0.0.1:8100/parse` с телом `{"url": "https://example.com"}`.

## Переменные окружения Ledger (контейнер `api` / локально)

| Переменная | Назначение |
|------------|------------|
| `PARSER_SERVICE_URL` | Базовый URL микросервиса (в Compose: `http://parser:8100`) |
| `CELERY_BROKER_URL` | Redis для брокера (`redis://redis:6379/0`) |
| `CELERY_RESULT_BACKEND` | Redis для результатов (`redis://redis:6379/1`) |
| `DATABASE_URL` | PostgreSQL Ledger |

## Локальный запуск без Docker

Потребуются работающие PostgreSQL и Redis, установка зависимостей `practice_1_3/requirements.txt`, переменные как в таблице с `localhost`, отдельный процесс:

```bash
celery -A app.bootstrap_celery:celery_app worker --loglevel=info
```

и микросервис парсера (`uvicorn main:app --port 8100` из `parser_service`).

Подробности и обоснование архитектуры — в [документации MkDocs `docs/lr3.md`](../docs/lr3.md).
