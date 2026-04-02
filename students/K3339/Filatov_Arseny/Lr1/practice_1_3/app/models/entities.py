from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field as PydanticField
from sqlmodel import Field, Relationship, SQLModel


class TransactionKind(str, Enum):
    income = "income"
    expense = "expense"


class UserBase(SQLModel):
    email: str = Field(index=True, unique=True, max_length=255)
    full_name: str = Field(max_length=120)


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    password_hash: str = Field(max_length=255)
    wallets: list["Wallet"] = Relationship(back_populates="owner")
    categories: list["Category"] = Relationship(back_populates="owner")
    transactions: list["FinTransaction"] = Relationship(back_populates="owner")


class UserRegister(SQLModel):
    email: str = Field(max_length=255)
    full_name: str = Field(max_length=120)
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(SQLModel):
    email: str | None = Field(default=None, max_length=255)
    full_name: str | None = Field(default=None, max_length=120)


class PasswordChange(SQLModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class WalletBase(SQLModel):
    label: str = Field(max_length=80)
    currency_code: str = Field(max_length=3)
    user_id: int | None = Field(default=None, foreign_key="user.id")


class Wallet(WalletBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    owner: User | None = Relationship(back_populates="wallets")
    transactions: list["FinTransaction"] = Relationship(back_populates="wallet")


class CategoryBase(SQLModel):
    name: str = Field(max_length=60)
    spending_cap: float | None = Field(default=None, ge=0)
    user_id: int | None = Field(default=None, foreign_key="user.id")


class Category(CategoryBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    owner: User | None = Relationship(back_populates="categories")
    transactions: list["FinTransaction"] = Relationship(back_populates="category")


class TagBase(SQLModel):
    name: str = Field(max_length=40, unique=True)


class TransactionTagLink(SQLModel, table=True):
    __tablename__ = "transaction_tag_link"

    transaction_id: int | None = Field(
        default=None,
        foreign_key="fin_transaction.id",
        primary_key=True,
    )
    tag_id: int | None = Field(default=None, foreign_key="tag.id", primary_key=True)
    linked_at: datetime = Field(default_factory=datetime.utcnow)
    label_note: str | None = Field(default=None, max_length=120)


class Tag(TagBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    transactions: list["FinTransaction"] = Relationship(
        back_populates="tags",
        link_model=TransactionTagLink,
    )


class FinTransactionBase(SQLModel):
    memo: str = Field(max_length=120)
    value: float = Field(gt=0)
    kind: TransactionKind
    booked_at: datetime
    note: str | None = Field(default=None, max_length=500)
    user_id: int | None = Field(default=None, foreign_key="user.id")
    wallet_id: int | None = Field(default=None, foreign_key="wallet.id")
    category_id: int | None = Field(default=None, foreign_key="category.id")


class FinTransaction(FinTransactionBase, table=True):
    __tablename__ = "fin_transaction"

    id: int | None = Field(default=None, primary_key=True)
    owner: User | None = Relationship(back_populates="transactions")
    wallet: Wallet | None = Relationship(back_populates="transactions")
    category: Category | None = Relationship(back_populates="transactions")
    tags: list[Tag] = Relationship(
        back_populates="transactions",
        link_model=TransactionTagLink,
    )


class FinTransactionCreate(SQLModel):
    memo: str = Field(max_length=120)
    value: float = Field(gt=0)
    kind: TransactionKind
    booked_at: datetime
    note: str | None = Field(default=None, max_length=500)
    wallet_id: int | None = None
    category_id: int | None = None
    tag_ids: list[int] = PydanticField(default_factory=list)


class FinTransactionUpdate(SQLModel):
    memo: str | None = Field(default=None, max_length=120)
    value: float | None = Field(default=None, gt=0)
    kind: TransactionKind | None = None
    booked_at: datetime | None = None
    note: str | None = Field(default=None, max_length=500)
    wallet_id: int | None = None
    category_id: int | None = None
    tag_ids: list[int] | None = None


class WalletPayload(SQLModel):
    label: str = Field(max_length=80)
    currency_code: str = Field(max_length=3)


class WalletUpdate(SQLModel):
    label: str | None = Field(default=None, max_length=80)
    currency_code: str | None = Field(default=None, max_length=3)


class CategoryPayload(SQLModel):
    name: str = Field(max_length=60)
    spending_cap: float | None = Field(default=None, ge=0)


class CategoryUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=60)
    spending_cap: float | None = Field(default=None, ge=0)


class TagCreate(TagBase):
    pass


class TagUpdate(SQLModel):
    name: str | None = Field(default=None, max_length=40)


class WalletRead(WalletBase):
    id: int


class CategoryRead(CategoryBase):
    id: int


class TagRead(TagBase):
    id: int


class UserRead(UserBase):
    id: int


class UserReadNested(UserRead):
    wallets: list[WalletRead] = PydanticField(default_factory=list)
    categories: list[CategoryRead] = PydanticField(default_factory=list)


class WalletReadNested(WalletRead):
    owner: UserRead | None = None


class CategoryReadNested(CategoryRead):
    owner: UserRead | None = None


class TagReadWithLink(TagRead):
    linked_at: datetime
    label_note: str | None = None


class FinTransactionRead(FinTransactionBase):
    id: int


class FinTransactionReadNested(FinTransactionRead):
    owner: UserRead | None = None
    wallet: WalletRead | None = None
    category: CategoryRead | None = None
    tags: list[TagReadWithLink] = PydanticField(default_factory=list)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
