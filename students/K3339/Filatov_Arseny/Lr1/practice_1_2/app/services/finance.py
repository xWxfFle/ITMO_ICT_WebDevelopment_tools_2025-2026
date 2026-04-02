from collections.abc import Sequence

from sqlmodel import Session, select

from app.models import (
    CategoryRead,
    FinTransaction,
    FinTransactionReadNested,
    TagReadWithLink,
    TransactionTagLink,
    UserRead,
    WalletRead,
)


def serialize_fin_transaction(session: Session, row: FinTransaction) -> FinTransactionReadNested:
    links = session.exec(
        select(TransactionTagLink).where(TransactionTagLink.transaction_id == row.id)
    ).all()
    by_tag = {link.tag_id: link.linked_at for link in links}
    tags_out: list[TagReadWithLink] = []
    for tag in row.tags:
        if tag.id in by_tag:
            tags_out.append(
                TagReadWithLink(id=tag.id, name=tag.name, linked_at=by_tag[tag.id]),
            )
    return FinTransactionReadNested(
        id=row.id,
        memo=row.memo,
        value=row.value,
        kind=row.kind,
        booked_at=row.booked_at,
        note=row.note,
        user_id=row.user_id,
        wallet_id=row.wallet_id,
        category_id=row.category_id,
        owner=UserRead.model_validate(row.owner) if row.owner else None,
        wallet=WalletRead.model_validate(row.wallet) if row.wallet else None,
        category=CategoryRead.model_validate(row.category) if row.category else None,
        tags=tags_out,
    )


def replace_transaction_tags(
    session: Session,
    transaction: FinTransaction,
    tag_ids: Sequence[int],
) -> None:
    existing = session.exec(
        select(TransactionTagLink).where(TransactionTagLink.transaction_id == transaction.id)
    ).all()
    for link in existing:
        session.delete(link)
    session.flush()
    for tid in tag_ids:
        session.add(TransactionTagLink(transaction_id=transaction.id, tag_id=tid))
