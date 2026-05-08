from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import requests
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, HttpUrl
from sqlmodel import Session

from config import settings
from db_models import ParsedWebTitle, get_engine, init_tables
from html_title import extract_title

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("parser-service")

_engine = None


def get_db_engine():
    global _engine
    if _engine is None:
        _engine = get_engine(settings.database_url)
    return _engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    engine = get_db_engine()
    init_tables(engine)
    log.info("Таблица lr2_parsed_web_title создана или уже существует")
    yield


app = FastAPI(
    title="HTML Parser Microservice — LR3",
    version="1.0.0",
    lifespan=lifespan,
)


class ParseRequest(BaseModel):
    url: HttpUrl


class ParseResponse(BaseModel):
    message: str = "Parsing completed"
    url: str
    title: str
    record_id: int


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/parse", response_model=ParseResponse)
def parse(req: ParseRequest) -> ParseResponse:
    url_str = str(req.url)

    headers = {"User-Agent": "lr3-parser-microservice/1.0"}

    try:
        response = requests.get(url_str, timeout=45, headers=headers)
        response.raise_for_status()
    except requests.RequestException as exc:
        log.exception("HTTP error for %s", url_str)
        raise HTTPException(status_code=502, detail=f"Не удалось загрузить страницу: {exc}") from exc

    title_raw = extract_title(response.text) or "(без title)"
    title = title_raw[:512]
    row = ParsedWebTitle(url=url_str[:2048], title=title)

    engine = get_db_engine()
    with Session(engine) as session:
        session.add(row)
        session.commit()
        session.refresh(row)

    log.info("Сохранено: %s -> %s", url_str[:80], title[:80])
    return ParseResponse(url=url_str, title=title, record_id=row.id)


@app.post("/parse-raw-url", response_model=ParseResponse)
def parse_raw_url(url: str = Query(..., min_length=4, max_length=2048)) -> ParseResponse:
    """Пример как в методичке: POST с параметром запроса ``url``."""
    parsed = ParseRequest.model_validate({"url": url})
    return parse(parsed)

