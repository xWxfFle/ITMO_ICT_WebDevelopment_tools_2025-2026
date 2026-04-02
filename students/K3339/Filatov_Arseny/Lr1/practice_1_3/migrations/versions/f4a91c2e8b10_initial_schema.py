"""initial schema

Revision ID: f4a91c2e8b10
Revises:
Create Date: 2026-04-02

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM

revision: str = "f4a91c2e8b10"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Один раз создаём тип; в create_table колонка с create_type=False, иначе SQLAlchemy
    # снова шлёт CREATE TYPE с checkfirst=False и падает на «already exists».
    transaction_kind = PG_ENUM("income", "expense", name="transactionkind")
    transaction_kind.create(op.get_bind(), checkfirst=True)
    transaction_kind_col = PG_ENUM(
        "income", "expense", name="transactionkind", create_type=False
    )

    op.create_table(
        "user",
        sa.Column("email", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("full_name", sqlmodel.sql.sqltypes.AutoString(length=120), nullable=False),
        sa.Column("password_hash", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=True)

    op.create_table(
        "tag",
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=40), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "wallet",
        sa.Column("label", sqlmodel.sql.sqltypes.AutoString(length=80), nullable=False),
        sa.Column("currency_code", sqlmodel.sql.sqltypes.AutoString(length=3), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "category",
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(length=60), nullable=False),
        sa.Column("spending_cap", sa.Float(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "fin_transaction",
        sa.Column("memo", sqlmodel.sql.sqltypes.AutoString(length=120), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("kind", transaction_kind_col, nullable=False),
        sa.Column("booked_at", sa.DateTime(), nullable=False),
        sa.Column("note", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("wallet_id", sa.Integer(), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["category.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.ForeignKeyConstraint(["wallet_id"], ["wallet.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "transaction_tag_link",
        sa.Column("transaction_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.Column("linked_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["tag_id"], ["tag.id"]),
        sa.ForeignKeyConstraint(["transaction_id"], ["fin_transaction.id"]),
        sa.PrimaryKeyConstraint("transaction_id", "tag_id"),
    )


def downgrade() -> None:
    op.drop_table("transaction_tag_link")
    op.drop_table("fin_transaction")
    op.drop_table("category")
    op.drop_table("wallet")
    op.drop_table("tag")
    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.drop_table("user")

    transaction_kind = PG_ENUM("income", "expense", name="transactionkind")
    transaction_kind.drop(op.get_bind(), checkfirst=True)
