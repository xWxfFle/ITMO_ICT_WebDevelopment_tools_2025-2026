"""Точка входа Celery-воркера: импорт задач после конфигурирования приложения."""

from app.celery_app import celery_app
from app.tasks import parse_tasks as _parse_tasks  # noqa: F401

__all__ = ["celery_app"]
