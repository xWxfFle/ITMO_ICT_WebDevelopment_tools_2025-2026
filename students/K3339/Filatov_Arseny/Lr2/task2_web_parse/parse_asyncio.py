"""
Параллельный парсинг через ``asyncio`` и ``aiohttp``: части URL обрабатываются
конкурентно; внутри части запросы идут последовательно ``await``.
Одна ``ClientSession`` на запуск задаётся через ``contextvars`` — сигнатура
``parse_and_save(url)`` остаётся как в методичке.
"""

from __future__ import annotations

import asyncio
import contextvars
import os
import time

import aiohttp
from sqlmodel import Session

from chunk_urls import split_into_chunks
from db_common import ParsedWebTitle, get_engine, init_db
from html_title import extract_title
from urls import URLS

NUM_WORKERS = int(os.environ.get("LR2_PARSE_WORKERS", "4"))

_aio_session: contextvars.ContextVar[aiohttp.ClientSession] = contextvars.ContextVar(
    "lr2_aiohttp_session",
)


async def parse_and_save(url: str) -> None:
    session = _aio_session.get()
    timeout = aiohttp.ClientTimeout(total=45)
    async with session.get(url, timeout=timeout) as response:
        response.raise_for_status()
        text = await response.text()
    title = extract_title(text) or "(без title)"
    engine = get_engine()
    row = ParsedWebTitle(url=url[:2048], title=title[:512])
    with Session(engine) as session_db:
        session_db.add(row)
        session_db.commit()
    print(f"[asyncio] {url} -> {title[:100]!r}")


async def process_chunk(chunk: list[str]) -> None:
    for url in chunk:
        try:
            await parse_and_save(url)
        except Exception as exc:  # noqa: BLE001
            print(f"[asyncio] Ошибка {url}: {exc}")


async def main_async() -> None:
    init_db()
    chunks = split_into_chunks(URLS, min(NUM_WORKERS, len(URLS)))
    headers = {"User-Agent": "lr2-parse/1.0"}
    t0 = time.perf_counter()
    async with aiohttp.ClientSession(headers=headers) as session:
        token = _aio_session.set(session)
        try:
            await asyncio.gather(*(process_chunk(c) for c in chunks))
        finally:
            _aio_session.reset(token)
    print(
        f"[asyncio] всего ссылок={len(URLS)} конвейеров={len(chunks)} "
        f"время={time.perf_counter() - t0:.3f}s"
    )


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
