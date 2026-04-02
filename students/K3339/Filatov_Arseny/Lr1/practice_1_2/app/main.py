from fastapi import FastAPI

from app.api.routers import categories, tags, transactions, users, wallets
from app.db.session import init_db

app = FastAPI(
    title="Ledger API — practice 1.2",
    description="PostgreSQL + SQLModel, доменная модель с кошельками и транзакциями.",
    version="0.2.0",
)

app.include_router(users.router)
app.include_router(wallets.router)
app.include_router(categories.router)
app.include_router(tags.router)
app.include_router(transactions.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/")
def root() -> str:
    return "Ledger API — practice 1.2 (PostgreSQL + SQLModel)"
