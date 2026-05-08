# Лабораторная работа 2 — параллелизм и парсинг

## Задание 1 — сумма 1…N

Папка `task1_sum/`. Верхняя граница **N = 10_000_000_000_000**. Прямой перебор всех слагаемых невозможен; в `calculate_sum(start, end)` используется формула суммы арифметической прогрессии на отрезке:

\\[
\\sum_{i=a}^{b} i = \\frac{b(b+1)}{2} - \\frac{(a-1)a}{2}
\\]

Интервал `[1, N]` режется на несколько подынтервалов; каждый подынтервал считается в отдельной задаче (поток / процесс / `asyncio.to_thread`).

Запуск (из каталога `task1_sum`):

```bash
python sum_threading.py
python sum_multiprocessing.py
python sum_asyncio.py
```

## Задание 2 — парсинг в PostgreSQL ЛР1

Папка `task2_web_parse/`. Используется **тот же URL БД**, что и в `practice_1_3` (переменная `DATABASE_URL` или значение по умолчанию в `db_common.py`). Создаётся отдельная таблица **`lr2_parsed_web_title`** (не смешивается с сущностями Ledger).

Зависимости:

```bash
pip install -r requirements.txt
```

Запуск:

```bash
cd task2_web_parse
set DATABASE_URL=postgresql://user:pass@host:5432/dbname
set LR2_PARSE_WORKERS=4
python parse_threading.py
python parse_multiprocessing.py
python parse_asyncio.py
```

Список URL — в `urls.py`; число «конвейеров» (частей списка) задаётся `LR2_PARSE_WORKERS`.

## Замеры времени

Таблицы с результатами замеров перенесены в [документацию в `docs/lr2.md`](../docs/lr2.md), чтобы не дублировать числа в двух местах.
