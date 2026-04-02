from fastapi import FastAPI

from app.api.routers import auth, categories, tags, transactions, users, wallets

app = FastAPI(
    title="Ledger API — practice 1.3",
    description="PostgreSQL, Alembic, JWT и изоляция данных по пользователю.",
    version="0.3.0",
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(wallets.router)
app.include_router(categories.router)
app.include_router(tags.router)
app.include_router(transactions.router)


@app.get("/")
def root() -> str:
    return "Ledger API — practice 1.3 (Alembic + JWT)"
