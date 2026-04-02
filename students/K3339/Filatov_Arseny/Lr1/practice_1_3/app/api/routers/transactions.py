from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.api.deps import get_current_user
from app.db.session import get_session
from app.models import (
    Category,
    FinTransaction,
    FinTransactionCreate,
    FinTransactionReadNested,
    FinTransactionUpdate,
    Tag,
    TransactionTagLink,
    User,
    Wallet,
)
from app.services.finance import replace_transaction_tags, serialize_fin_transaction

router = APIRouter(prefix="/transactions", tags=["transactions"])


def _tx_owned(session: Session, tx_id: int, owner_id: int) -> FinTransaction:
    stmt = (
        select(FinTransaction)
        .where(FinTransaction.id == tx_id)
        .options(
            selectinload(FinTransaction.owner),
            selectinload(FinTransaction.wallet),
            selectinload(FinTransaction.category),
            selectinload(FinTransaction.tags),
        )
    )
    row = session.exec(stmt).first()
    if not row or row.user_id != owner_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return row


def _wallet_belongs(session: Session, wallet_id: int, owner_id: int) -> Wallet:
    w = session.get(Wallet, wallet_id)
    if not w or w.user_id != owner_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid wallet for this user")
    return w


def _category_belongs(session: Session, category_id: int, owner_id: int) -> Category:
    c = session.get(Category, category_id)
    if not c or c.user_id != owner_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid category for this user")
    return c


def _validate_tag_ids(session: Session, tag_ids: Sequence[int]) -> None:
    for tid in tag_ids:
        if session.get(Tag, tid) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown tag id {tid}")


@router.get("", response_model=list[FinTransactionReadNested])
def list_my_transactions(
    session: Annotated[Session, Depends(get_session)],
    current: Annotated[User, Depends(get_current_user)],
) -> list[FinTransactionReadNested]:
    stmt = (
        select(FinTransaction)
        .where(FinTransaction.user_id == current.id)
        .options(
            selectinload(FinTransaction.owner),
            selectinload(FinTransaction.wallet),
            selectinload(FinTransaction.category),
            selectinload(FinTransaction.tags),
        )
    )
    rows = session.exec(stmt).all()
    return [serialize_fin_transaction(session, r) for r in rows]


@router.get("/{transaction_id}", response_model=FinTransactionReadNested)
def get_transaction(
    transaction_id: int,
    session: Annotated[Session, Depends(get_session)],
    current: Annotated[User, Depends(get_current_user)],
) -> FinTransactionReadNested:
    row = _tx_owned(session, transaction_id, current.id)
    return serialize_fin_transaction(session, row)


@router.post("", response_model=FinTransactionReadNested, status_code=status.HTTP_201_CREATED)
def create_transaction(
    body: FinTransactionCreate,
    session: Annotated[Session, Depends(get_session)],
    current: Annotated[User, Depends(get_current_user)],
) -> FinTransactionReadNested:
    _wallet_belongs(session, body.wallet_id, current.id)  # type: ignore[arg-type]
    _category_belongs(session, body.category_id, current.id)  # type: ignore[arg-type]
    _validate_tag_ids(session, body.tag_ids)
    row = FinTransaction(
        memo=body.memo,
        value=body.value,
        kind=body.kind,
        booked_at=body.booked_at,
        note=body.note,
        user_id=current.id,
        wallet_id=body.wallet_id,
        category_id=body.category_id,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    replace_transaction_tags(session, row, body.tag_ids)
    session.commit()
    row = _tx_owned(session, row.id, current.id)  # type: ignore[arg-type]
    return serialize_fin_transaction(session, row)


@router.patch("/{transaction_id}", response_model=FinTransactionReadNested)
def update_transaction(
    transaction_id: int,
    body: FinTransactionUpdate,
    session: Annotated[Session, Depends(get_session)],
    current: Annotated[User, Depends(get_current_user)],
) -> FinTransactionReadNested:
    row = _tx_owned(session, transaction_id, current.id)
    data = body.model_dump(exclude_unset=True, exclude={"tag_ids"})
    wid = data.get("wallet_id", row.wallet_id)
    cid = data.get("category_id", row.category_id)
    if "wallet_id" in data:
        _wallet_belongs(session, wid, current.id)  # type: ignore[arg-type]
    if "category_id" in data:
        _category_belongs(session, cid, current.id)  # type: ignore[arg-type]
    for k, v in data.items():
        setattr(row, k, v)
    session.add(row)
    session.commit()
    session.refresh(row)
    if body.tag_ids is not None:
        _validate_tag_ids(session, body.tag_ids)
        replace_transaction_tags(session, row, body.tag_ids)
        session.commit()
    row = _tx_owned(session, transaction_id, current.id)
    return serialize_fin_transaction(session, row)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: int,
    session: Annotated[Session, Depends(get_session)],
    current: Annotated[User, Depends(get_current_user)],
) -> Response:
    row = _tx_owned(session, transaction_id, current.id)
    links = session.exec(
        select(TransactionTagLink).where(TransactionTagLink.transaction_id == row.id)
    ).all()
    for link in links:
        session.delete(link)
    session.delete(row)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
