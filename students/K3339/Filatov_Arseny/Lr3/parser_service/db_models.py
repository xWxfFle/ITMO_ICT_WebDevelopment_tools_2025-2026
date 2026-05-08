"""Таблица совпадает по имени с ЛР2 (`lr2_parsed_web_title`) для совместности с дампами."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel, create_engine

DEFAULT_DB_URL = "postgresql://ledger:ledger@localhost:5432/ledger"


def get_database_url(url: Optional[str]) -> str:
    return url if url else DEFAULT_DB_URL


def get_engine(database_url: str):
    return create_engine(database_url, echo=False)


class ParsedWebTitle(SQLModel, table=True):
    __tablename__ = "lr2_parsed_web_title"

    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(index=True, max_length=2048)
    title: str = Field(max_length=512)
    fetched_at: datetime = Field(default_factory=datetime.utcnow)


def init_tables(engine):
    SQLModel.metadata.create_all(engine)
