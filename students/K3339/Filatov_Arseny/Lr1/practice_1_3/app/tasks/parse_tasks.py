from __future__ import annotations

import httpx

from app.celery_app import celery_app
from app.core.config import settings


@celery_app.task(name="parser.fetch_and_store")
def fetch_page_title(url: str) -> dict:
    """Вызывает микросервис парсера по HTTP и возвращает JSON-ответ (кладёт задачу вне API)."""

    endpoint = settings.parser_service_url.rstrip("/") + "/parse"
    with httpx.Client(timeout=60.0, follow_redirects=True) as client:
        response = client.post(endpoint, json={"url": url})
        response.raise_for_status()
        return response.json()
