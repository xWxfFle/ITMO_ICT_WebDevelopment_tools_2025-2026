# Practice 1.3 — Ledger API (Alembic, JWT)

Подробная веб-документация: `../../docs/practice_1_3.md`. Кратко:

## Миграции (Windows / PowerShell)

Если команда `alembic` не находится, используйте модуль Python из venv:

```powershell
cd Lr1\practice_1_3
..\.venv\Scripts\python.exe -m alembic upgrade head
```

Или активируйте venv из `Lr1`, затем:

```powershell
python -m alembic upgrade head
```

## Запуск

```powershell
python -m uvicorn app.main:app --reload
```

`.env` в этой папке: см. `.env.example`. Полный гайд: `../GUIDE.md`.
