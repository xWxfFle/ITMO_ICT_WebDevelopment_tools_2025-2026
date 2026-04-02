"""add label_note to transaction_tag_link

Revision ID: g5b02d3f9c21
Revises: f4a91c2e8b10
Create Date: 2026-04-02

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

revision: str = "g5b02d3f9c21"
down_revision: Union[str, Sequence[str], None] = "f4a91c2e8b10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "transaction_tag_link",
        sa.Column("label_note", sqlmodel.sql.sqltypes.AutoString(length=120), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("transaction_tag_link", "label_note")
