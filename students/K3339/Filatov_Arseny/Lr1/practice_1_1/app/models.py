from datetime import date
from enum import Enum

from pydantic import BaseModel, Field


class TransactionKind(str, Enum):
    income = "income"
    expense = "expense"


class Wallet(BaseModel):
    id: int
    label: str = Field(..., min_length=2, max_length=80)
    currency_code: str = Field(..., min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")


class WalletCreate(BaseModel):
    label: str = Field(..., min_length=2, max_length=80)
    currency_code: str = Field(..., min_length=3, max_length=3, pattern=r"^[A-Z]{3}$")


class Category(BaseModel):
    id: int
    name: str = Field(..., min_length=2, max_length=60)
    spending_cap: float | None = Field(default=None, ge=0)


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=60)
    spending_cap: float | None = Field(default=None, ge=0)


class Tag(BaseModel):
    id: int
    name: str = Field(..., min_length=2, max_length=40)


class TagCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=40)


class Transaction(BaseModel):
    id: int
    memo: str = Field(..., min_length=2, max_length=120)
    value: float = Field(..., gt=0)
    kind: TransactionKind
    booked_on: date
    wallet: Wallet
    category: Category
    tags: list[Tag] = Field(default_factory=list)
    note: str | None = Field(default=None, max_length=500)


class TransactionCreate(BaseModel):
    memo: str = Field(..., min_length=2, max_length=120)
    value: float = Field(..., gt=0)
    kind: TransactionKind
    booked_on: date
    wallet: Wallet
    category: Category
    tags: list[TagCreate] = Field(default_factory=list)
    note: str | None = Field(default=None, max_length=500)
