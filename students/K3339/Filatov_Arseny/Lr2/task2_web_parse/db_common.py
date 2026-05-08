"""Подключение к той же PostgreSQL, что и в ЛР1, и таблица для результатов парсинга."""

from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from sqlmodel import Field, Session, SQLModel, create_engine

# Совпадает с дефолтом ``practice_1_3``; переопределите через переменную окружения.
DEFAULT_DB_URL = "postgresql://postgres@localhost:5432/filatov_finance_p13"


def database_url() -> str:
    return os.environ.get("DATABASE_URL", DEFAULT_DB_URL)


def get_engine():
    return create_engine(database_url(), echo=False)


class ParsedWebTitle(SQLModel, table=True):
    """Заголовки страниц, спарсенные в рамках ЛР2 (отдельно от сущностей Ledger)."""

    __tablename__ = "lr2_parsed_web_title"

    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(index=True, max_length=2048)
    title: str = Field(max_length=512)
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


def init_db() -> None:
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
