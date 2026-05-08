from __future__ import annotations

from typing import Any

import httpx
from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl

from app.celery_app import celery_app
from app.core.config import settings
from app.tasks.parse_tasks import fetch_page_title

router = APIRouter(prefix="/integrations/parser", tags=["parser-integration"])


class ParserUrlPayload(BaseModel):
    url: HttpUrl


def _proxy_to_parser(payload: ParserUrlPayload) -> dict[str, Any]:
    endpoint = settings.parser_service_url.rstrip("/") + "/parse"
    try:
        with httpx.Client(timeout=60.0, follow_redirects=True) as client:
            response = client.post(endpoint, json={"url": str(payload.url)})
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text or str(exc.response.status_code)
        raise HTTPException(status_code=502, detail=detail) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Ошибка HTTP-клиента: {exc}") from exc


@router.post("/sync")
def parse_sync(payload: ParserUrlPayload) -> dict[str, Any]:
    """Подзадача 2 ЛР3: синхронный запрос Ledger → парсер (отдельный контейнер) → результат."""
    return _proxy_to_parser(payload)


@router.post("/async")
def parse_enqueue(payload: ParserUrlPayload) -> dict[str, str]:
    """Подзадача 3 ЛР3: постановка задачи парсера в очередь Redis / Celery."""
    async_result = fetch_page_title.delay(str(payload.url))
    return {"task_id": async_result.id, "status": "queued"}


@router.get("/async/{task_id}")
def parse_async_status(task_id: str) -> dict[str, Any]:
    async_result = AsyncResult(task_id, app=celery_app)
    out: dict[str, Any] = {
        "task_id": task_id,
        "state": async_result.state,
    }
    if async_result.ready():
        if async_result.successful():
            out["result"] = async_result.result
        else:
            out["error"] = str(async_result.info)
    return out
