# Практика 1.3 — Alembic, JWT, облачная БД

## Назначение

Финальная версия лабораторной ветки: схема БД управляется **миграциями Alembic**, секреты и URL базы — через **`.env`**, пользователи **регистрируются** с хэшем пароля, доступ к API защищён **JWT** (Bearer). Кошельки, категории и транзакции видны только **владельцу**.

---

## Технологии

| Область | Пакеты |
|---------|--------|
| API | FastAPI, Uvicorn, python-multipart |
| ORM и БД | SQLModel, psycopg2-binary |
| Миграции | Alembic |
| Конфиг | python-dotenv, pydantic-settings |
| Безопасность | passlib[bcrypt], python-jose[cryptography] |

Файл: `Lr1/practice_1_3/requirements.txt`. Шаблон окружения: `Lr1/practice_1_3/.env.example`.

---

## Структура проекта

Относительно `Lr1/practice_1_3/`:

```text
practice_1_3/
├── .env.example
├── alembic.ini
├── requirements.txt
├── README.md
├── migrations/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── f4a91c2e8b10_initial_schema.py
│       └── g5b02d3f9c21_add_label_note_to_tag_link.py
└── app/
    ├── main.py
    ├── core/
    │   ├── config.py      # Settings из .env
    │   └── security.py    # bcrypt, JWT
    ├── db/session.py
    ├── models/entities.py
    ├── api/
    │   ├── deps.py        # get_current_user + OAuth2 Bearer
    │   └── routers/
    │       ├── auth.py
    │       ├── users.py
    │       ├── wallets.py
    │       ├── categories.py
    │       ├── tags.py
    │       └── transactions.py
    └── services/finance.py
```

---

## Миграции Alembic

1. **Начальная схема** — все таблицы, в том числе `transaction_tag_link` с полем `linked_at`.
2. **Вторая ревизия** — добавление поля **`label_note`** в `transaction_tag_link` (расширение ассоциативной сущности).

Команды выполняются **из каталога `practice_1_3`**, чтобы подхватился локальный `.env`:

```bash
cd Lr1/practice_1_3
python -m alembic upgrade head
```

На Windows, если команда `alembic` «не найдена», используйте именно **`python -m alembic`**, где `python` из виртуального окружения, в котором выполнен `pip install -r requirements.txt` (например после `Lr1\.venv\Scripts\Activate.ps1`).

Реальный `DATABASE_URL` подставляется в `migrations/env.py` из переменной окружения и **перекрывает** запасное значение в `alembic.ini`.

---

## Файл `.env`

Создайте `Lr1/practice_1_3/.env` (не коммитить). Минимальный набор:

```env
DATABASE_URL=postgresql://...
SECRET_KEY=длинная-случайная-строка
ACCESS_TOKEN_EXPIRE_MINUTES=120
```

- **DATABASE_URL** — из консоли Neon или вашего Postgres; для Neon обычно нужен `sslmode=require`.
- **SECRET_KEY** — для подписи JWT; в репозиторий не класть.

---

## Установка, миграции, запуск

```bash
cd Lr1/practice_1_3
pip install -r requirements.txt
# создать и заполнить .env
alembic upgrade head
uvicorn app.main:app --reload
```

**Swagger:** `http://127.0.0.1:8000/docs`

---

## Аутентификация и порядок проверки в UI

1. **POST `/auth/register`** — тело JSON: `email`, `full_name`, `password` (минимум 8 символов).
2. **POST `/auth/login`** — форма OAuth2: поле **username** = email, **password** = пароль. В ответе `access_token`.
3. В Swagger нажать **Authorize**, схема Bearer, значение: `Bearer <access_token>` (или только токен — зависит от версии UI; обычно полный `Bearer ...`).
4. Дальше вызывать защищённые маршруты: кошельки, категории, теги, транзакции, список пользователей и т.д.

Публичные без токена: только `/`, `/auth/register`, `/auth/login`.

---

## Основные маршруты

| Группа | Назначение |
|--------|------------|
| `/auth/*` | Регистрация и выдача JWT |
| `/users/me` | Профиль текущего пользователя |
| `/users/me/password` | Смена пароля (старый + новый) |
| `/users` | Список пользователей (нужен токен) |
| `/users/{id}` | Профиль с вложенными кошельками и категориями |
| `/users/{id}` PATCH/DELETE | Обновление / удаление **только своей** учётки |
| `/wallets`, `/categories`, `/tags`, `/transactions` | CRUD в рамках данных **текущего** пользователя |

---

## Связь с предыдущими этапами

- [Практика 1.1](practice_1_1.md) — прототип без БД.  
- [Практика 1.2](practice_1_2.md) — та же доменная модель без JWT и без Alembic.  
- **Практика 1.3** — целевая сдача по критериям с миграциями и пользовательским функционалом на 15 баллов.
