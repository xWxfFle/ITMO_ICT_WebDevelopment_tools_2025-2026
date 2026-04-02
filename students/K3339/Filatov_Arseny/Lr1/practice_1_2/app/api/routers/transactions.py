from collections.abc import Sequence

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.api.deps import get_session
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


def _tx_or_404(session: Session, tx_id: int) -> FinTransaction:
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
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    return row


def _require_fk(session: Session, *, user_id: int | None, wallet_id: int | None, category_id: int | None) -> None:
    if user_id is None or session.get(User, user_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user")
    if wallet_id is None or session.get(Wallet, wallet_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid wallet")
    if category_id is None or session.get(Category, category_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid category")


def _validate_tag_ids(session: Session, tag_ids: Sequence[int]) -> None:
    for tid in tag_ids:
        if session.get(Tag, tid) is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown tag id {tid}")


@router.get("", response_model=list[FinTransactionReadNested])
def list_transactions(session: Session = Depends(get_session)) -> list[FinTransactionReadNested]:
    stmt = select(FinTransaction).options(
        selectinload(FinTransaction.owner),
        selectinload(FinTransaction.wallet),
        selectinload(FinTransaction.category),
        selectinload(FinTransaction.tags),
    )
    rows = session.exec(stmt).all()
    return [serialize_fin_transaction(session, r) for r in rows]


@router.get("/{transaction_id}", response_model=FinTransactionReadNested)
def get_transaction(transaction_id: int, session: Session = Depends(get_session)) -> FinTransactionReadNested:
    row = _tx_or_404(session, transaction_id)
    return serialize_fin_transaction(session, row)


@router.post("", response_model=FinTransactionReadNested, status_code=status.HTTP_201_CREATED)
def create_transaction(
    body: FinTransactionCreate,
    session: Session = Depends(get_session),
) -> FinTransactionReadNested:
    _require_fk(session, user_id=body.user_id, wallet_id=body.wallet_id, category_id=body.category_id)
    _validate_tag_ids(session, body.tag_ids)
    payload = body.model_dump(exclude={"tag_ids"})
    row = FinTransaction.model_validate(payload)
    session.add(row)
    session.commit()
    session.refresh(row)
    replace_transaction_tags(session, row, body.tag_ids)
    session.commit()
    row = _tx_or_404(session, row.id)  # type: ignore[arg-type]
    return serialize_fin_transaction(session, row)


@router.patch("/{transaction_id}", response_model=FinTransactionReadNested)
def update_transaction(
    transaction_id: int,
    body: FinTransactionUpdate,
    session: Session = Depends(get_session),
) -> FinTransactionReadNested:
    row = _tx_or_404(session, transaction_id)
    data = body.model_dump(exclude_unset=True, exclude={"tag_ids"})
    uid = data.get("user_id", row.user_id)
    wid = data.get("wallet_id", row.wallet_id)
    cid = data.get("category_id", row.category_id)
    if "user_id" in data or "wallet_id" in data or "category_id" in data:
        _require_fk(session, user_id=uid, wallet_id=wid, category_id=cid)
    for k, v in data.items():
        setattr(row, k, v)
    session.add(row)
    session.commit()
    session.refresh(row)
    if body.tag_ids is not None:
        _validate_tag_ids(session, body.tag_ids)
        replace_transaction_tags(session, row, body.tag_ids)
        session.commit()
    row = _tx_or_404(session, transaction_id)
    return serialize_fin_transaction(session, row)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(transaction_id: int, session: Session = Depends(get_session)) -> Response:
    row = _tx_or_404(session, transaction_id)
    links = session.exec(
        select(TransactionTagLink).where(TransactionTagLink.transaction_id == row.id)
    ).all()
    for link in links:
        session.delete(link)
    session.delete(row)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
