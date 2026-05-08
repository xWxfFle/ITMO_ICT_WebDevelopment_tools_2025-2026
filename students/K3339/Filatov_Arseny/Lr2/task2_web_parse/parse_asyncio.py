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
from sqlalchemy.ext.asyncio import async_sessionmaker

from chunk_urls import split_into_chunks
from db_common import ParsedWebTitle, get_async_sessionmaker, init_db_async
from html_title import extract_title
from urls import URLS

NUM_WORKERS = int(os.environ.get("LR2_PARSE_WORKERS", "4"))

_aio_session: contextvars.ContextVar[aiohttp.ClientSession] = contextvars.ContextVar(
    "lr2_aiohttp_session",
)
_db_sessionmaker: contextvars.ContextVar[async_sessionmaker] = contextvars.ContextVar(
    "lr2_db_sessionmaker",
)


async def parse_and_save(url: str) -> None:
    session = _aio_session.get()
    sessionmaker = _db_sessionmaker.get()
    timeout = aiohttp.ClientTimeout(total=45)
    async with session.get(url, timeout=timeout) as response:
        response.raise_for_status()
        text = await response.text()
    title = extract_title(text) or "(без title)"
    row = ParsedWebTitle(url=url[:2048], title=title[:512])
    async with sessionmaker() as session_db:
        session_db.add(row)
        await session_db.commit()
    print(f"[asyncio] {url} -> {title[:100]!r}")


async def process_chunk(chunk: list[str]) -> None:
    for url in chunk:
        try:
            await parse_and_save(url)
        except Exception as exc:  # noqa: BLE001
            print(f"[asyncio] Ошибка {url}: {exc}")


async def main_async() -> None:
    await init_db_async()
    chunks = split_into_chunks(URLS, min(NUM_WORKERS, len(URLS)))
    headers = {"User-Agent": "lr2-parse/1.0"}
    sessionmaker = get_async_sessionmaker()
    t0 = time.perf_counter()
    async with aiohttp.ClientSession(headers=headers) as session:
        token_http = _aio_session.set(session)
        token_db = _db_sessionmaker.set(sessionmaker)
        try:
            await asyncio.gather(*(process_chunk(c) for c in chunks))
        finally:
            _aio_session.reset(token_http)
            _db_sessionmaker.reset(token_db)
    print(
        f"[asyncio] всего ссылок={len(URLS)} конвейеров={len(chunks)} "
        f"время={time.perf_counter() - t0:.3f}s"
    )


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
