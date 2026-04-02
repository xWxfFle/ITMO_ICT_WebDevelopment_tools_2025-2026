# Практика 1.2 — PostgreSQL и SQLModel

## Назначение

Вторая итерация: те же идеи предметной области, но данные хранятся в **PostgreSQL**, доступ — через **SQLModel** (ORM поверх SQLAlchemy). Реализованы связи **один-ко-многим** и **многие-ко-многим** с ассоциативной таблицей и дополнительным полем на связи.

Схема БД создаётся при старте приложения вызовом `SQLModel.metadata.create_all` (**без Alembic** на этом этапе).

---

## Технологии

| Компонент | Пакет |
|-----------|--------|
| API | FastAPI, Uvicorn |
| ORM | SQLModel, SQLAlchemy |
| Драйвер PostgreSQL | psycopg2-binary |
| Конфиг из файла | python-dotenv |

Файл зависимостей: `Lr1/practice_1_2/requirements.txt`.

---

## Структура проекта

Относительно `Lr1/practice_1_2/`:

```text
practice_1_2/
├── requirements.txt
├── README.md
└── app/
    ├── main.py
    ├── api/
    │   ├── deps.py
    │   └── routers/
    │       ├── users.py
    │       ├── wallets.py
    │       ├── categories.py
    │       ├── tags.py
    │       └── transactions.py
    ├── core/              # зарезервировано под общие настройки
    ├── db/
    │   └── session.py     # engine, get_session, init_db
    ├── models/
    │   ├── __init__.py
    │   └── entities.py    # таблицы и схемы Create/Read/Update
    └── services/
        └── finance.py     # сериализация транзакций и M:N link
```

---

## Модель данных (таблицы)

| Таблица | Назначение |
|---------|------------|
| `user` | Пользователь: email, full_name |
| `wallet` | Кошелёк, FK → `user` |
| `category` | Категория, лимит `spending_cap`, FK → `user` |
| `tag` | Глобальный справочник тегов (уникальное имя) |
| `fin_transaction` | Транзакция: сумма, тип, дата, FK → user, wallet, category |
| `transaction_tag_link` | Связь M:N транзакция ↔ тег; поле **`linked_at`** (время привязки) |

**GET** по пользователю, кошельку, категории и транзакции возвращает **вложенные** объекты где нужно (`selectinload`), для транзакций теги обогащаются данными из `transaction_tag_link`.

---

## Переменные окружения

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/ИМЯ_БД
```

Для [Neon](https://console.neon.tech) добавьте к URI параметр `sslmode=require`. Если соединение падает из‑за `channel_binding=require`, уберите его из строки (часто достаточно оставить только SSL).

---

## Установка и запуск

1. Создайте базу в PostgreSQL
2. Укажите `DATABASE_URL` в `.env` внутри `practice_1_2`.

```bash
cd Lr1/practice_1_2
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Swagger:** `http://127.0.0.1:8000/docs`

Пользователь на этом этапе **без пароля** — регистрация и JWT появляются в [практике 1.3](practice_1_3.md).

---

## HTTP API (группы маршрутов)

Все префиксы ниже от корня приложения (`/`).

| Префикс | Операции |
|---------|----------|
| `/users` | CRUD пользователей |
| `/wallets` | CRUD кошельков |
| `/categories` | CRUD категорий |
| `/tags` | CRUD тегов |
| `/transactions` | CRUD транзакций; ответы с вложенным user, wallet, category и тегами с `linked_at` |

Подробные пути и тела запросов удобнее смотреть в интерактивной документации `/docs`.

---

## Отличия от практики 1.1

- Данные **сохраняются** в БД.
- Код **разнесён** по модулям роутеров и сервису.
- Связь транзакций с тегами идёт через **id тегов** (`tag_ids`), а в ответе отдаётся время связи из link-таблицы.

---

## Что дальше

В [практике 1.3](practice_1_3.md) добавляются **Alembic**, **JWT**, **хэш пароля**, защита ресурсов по текущему пользователю; создание схемы переносится на миграции.
