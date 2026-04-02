from fastapi import FastAPI, HTTPException, Response, status

from app.models import (
    Category,
    CategoryCreate,
    Tag,
    TagCreate,
    Transaction,
    TransactionCreate,
    TransactionKind,
    Wallet,
    WalletCreate,
)

app = FastAPI(
    title="Ledger Lite (practice 1.1)",
    description="Учебный сервис личных финансов: in-memory слой без БД.",
    version="0.1.0",
)


wallets_db: list[Wallet] = [
    Wallet(id=1, label="Основной счёт", currency_code="RUB"),
    Wallet(id=2, label="Наличные", currency_code="RUB"),
]

categories_db: list[Category] = [
    Category(id=1, name="Зарплата", spending_cap=None),
    Category(id=2, name="Продукты", spending_cap=18000),
    Category(id=3, name="Транспорт", spending_cap=6000),
]

transactions_db: list[Transaction] = [
    Transaction(
        id=1,
        memo="Аванс за апрель",
        value=95000,
        kind=TransactionKind.income,
        booked_on="2026-04-01",
        wallet=wallets_db[0],
        category=categories_db[0],
        tags=[Tag(id=1, name="работа"), Tag(id=2, name="фикс")],
        note="Перевод от работодателя",
    ),
    Transaction(
        id=2,
        memo="Супермаркет",
        value=4200,
        kind=TransactionKind.expense,
        booked_on="2026-04-02",
        wallet=wallets_db[1],
        category=categories_db[1],
        tags=[Tag(id=3, name="еда"), Tag(id=4, name="семья")],
        note=None,
    ),
]


def _next_id(items: list, attr: str = "id") -> int:
    return max((getattr(x, attr) for x in items), default=0) + 1


def _next_tag_id() -> int:
    ids = [t.id for tr in transactions_db for t in tr.tags]
    return max(ids, default=0) + 1


def _wallet_index(wallet_id: int) -> int | None:
    for i, w in enumerate(wallets_db):
        if w.id == wallet_id:
            return i
    return None


def _category_index(category_id: int) -> int | None:
    for i, c in enumerate(categories_db):
        if c.id == category_id:
            return i
    return None


def _transaction_index(transaction_id: int) -> int | None:
    for i, t in enumerate(transactions_db):
        if t.id == transaction_id:
            return i
    return None


def _resolve_wallet(wallet: Wallet) -> Wallet:
    idx = _wallet_index(wallet.id)
    if idx is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown wallet id")
    return wallets_db[idx]


def _resolve_category(category: Category) -> Category:
    idx = _category_index(category.id)
    if idx is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unknown category id")
    return categories_db[idx]


def _build_tags(creates: list[TagCreate]) -> list[Tag]:
    base = _next_tag_id()
    return [Tag(id=base + i, name=tc.name) for i, tc in enumerate(creates)]


def _build_transaction(data: TransactionCreate, transaction_id: int) -> Transaction:
    wallet = _resolve_wallet(data.wallet)
    category = _resolve_category(data.category)
    tags = _build_tags(data.tags)
    return Transaction(
        id=transaction_id,
        memo=data.memo,
        value=data.value,
        kind=data.kind,
        booked_on=data.booked_on,
        wallet=wallet,
        category=category,
        tags=tags,
        note=data.note,
    )


@app.get("/")
def root() -> str:
    return "Ledger Lite API — practice 1.1"


@app.get("/wallets", response_model=list[Wallet])
def list_wallets() -> list[Wallet]:
    return wallets_db


@app.get("/wallets/{wallet_id}", response_model=Wallet)
def get_wallet(wallet_id: int) -> Wallet:
    idx = _wallet_index(wallet_id)
    if idx is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    return wallets_db[idx]


@app.post("/wallets", response_model=Wallet, status_code=status.HTTP_201_CREATED)
def create_wallet(body: WalletCreate) -> Wallet:
    w = Wallet(id=_next_id(wallets_db), **body.model_dump())
    wallets_db.append(w)
    return w


@app.put("/wallets/{wallet_id}", response_model=Wallet)
def replace_wallet(wallet_id: int, body: WalletCreate) -> Wallet:
    idx = _wallet_index(wallet_id)
    if idx is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    wallets_db[idx] = Wallet(id=wallet_id, **body.model_dump())
    _refresh_wallet_refs(wallet_id, wallets_db[idx])
    return wallets_db[idx]


@app.delete("/wallets/{wallet_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_wallet(wallet_id: int) -> Response:
    idx = _wallet_index(wallet_id)
    if idx is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    if any(t.wallet.id == wallet_id for t in transactions_db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wallet is referenced by transactions",
        )
    wallets_db.pop(idx)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _refresh_wallet_refs(wallet_id: int, new_wallet: Wallet) -> None:
    for i, tr in enumerate(transactions_db):
        if tr.wallet.id == wallet_id:
            transactions_db[i] = tr.model_copy(update={"wallet": new_wallet})


@app.get("/categories", response_model=list[Category])
def list_categories() -> list[Category]:
    return categories_db


@app.get("/categories/{category_id}", response_model=Category)
def get_category(category_id: int) -> Category:
    idx = _category_index(category_id)
    if idx is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return categories_db[idx]


@app.post("/categories", response_model=Category, status_code=status.HTTP_201_CREATED)
def create_category(body: CategoryCreate) -> Category:
    c = Category(id=_next_id(categories_db), **body.model_dump())
    categories_db.append(c)
    return c


@app.put("/categories/{category_id}", response_model=Category)
def replace_category(category_id: int, body: CategoryCreate) -> Category:
    idx = _category_index(category_id)
    if idx is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    categories_db[idx] = Category(id=category_id, **body.model_dump())
    new_c = categories_db[idx]
    for i, tr in enumerate(transactions_db):
        if tr.category.id == category_id:
            transactions_db[i] = tr.model_copy(update={"category": new_c})
    return new_c


@app.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_category(category_id: int) -> Response:
    idx = _category_index(category_id)
    if idx is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    if any(t.category.id == category_id for t in transactions_db):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category is referenced by transactions",
        )
    categories_db.pop(idx)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/transactions", response_model=list[Transaction])
def list_transactions() -> list[Transaction]:
    return transactions_db


@app.get("/transactions/{transaction_id}", response_model=Transaction)
def get_transaction(transaction_id: int) -> Transaction:
    idx = _transaction_index(transaction_id)
    if idx is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return transactions_db[idx]


@app.post("/transactions", response_model=Transaction, status_code=status.HTTP_201_CREATED)
def create_transaction(body: TransactionCreate) -> Transaction:
    tr = _build_transaction(body, _next_id(transactions_db))
    transactions_db.append(tr)
    return tr


@app.put("/transactions/{transaction_id}", response_model=Transaction)
def replace_transaction(transaction_id: int, body: TransactionCreate) -> Transaction:
    idx = _transaction_index(transaction_id)
    if idx is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    transactions_db[idx] = _build_transaction(body, transaction_id)
    return transactions_db[idx]


@app.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_transaction(transaction_id: int) -> Response:
    idx = _transaction_index(transaction_id)
    if idx is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    transactions_db.pop(idx)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
