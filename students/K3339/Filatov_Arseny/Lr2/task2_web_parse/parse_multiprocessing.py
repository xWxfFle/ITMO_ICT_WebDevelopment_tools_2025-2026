"""
Параллельный парсинг через ``multiprocessing``: каждый процесс обрабатывает свою
долю URL (внутри процесса запросы последовательные). Перед запуском вызывается
``init_db()`` в родителе; дочерние процессы создают своё подключение в ``parse_and_save``.
"""

from __future__ import annotations

import os
import time
from multiprocessing import Pool

import requests
from sqlmodel import Session

from chunk_urls import split_into_chunks
from db_common import ParsedWebTitle, get_engine, init_db
from html_title import extract_title
from urls import URLS

NUM_WORKERS = int(os.environ.get("LR2_PARSE_WORKERS", "4"))


def parse_and_save(url: str) -> None:
    engine = get_engine()
    response = requests.get(url, timeout=45, headers={"User-Agent": "lr2-parse/1.0"})
    response.raise_for_status()
    title = extract_title(response.text) or "(без title)"
    row = ParsedWebTitle(url=url[:2048], title=title[:512])
    with Session(engine) as session:
        session.add(row)
        session.commit()
    print(f"[multiprocessing] {url} -> {title[:100]!r}")


def process_chunk(chunk: list[str]) -> None:
    for url in chunk:
        try:
            parse_and_save(url)
        except Exception as exc:  # noqa: BLE001
            print(f"[multiprocessing] Ошибка {url}: {exc}")


def main() -> None:
    init_db()
    chunks = split_into_chunks(URLS, min(NUM_WORKERS, len(URLS)))
    t0 = time.perf_counter()
    with Pool(processes=len(chunks)) as pool:
        pool.map(process_chunk, chunks)
    print(
        f"[multiprocessing] всего ссылок={len(URLS)} процессов={len(chunks)} "
        f"время={time.perf_counter() - t0:.3f}s"
    )


if __name__ == "__main__":
    main()
