from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.api.deps import get_current_user
from app.db.session import get_session
from app.models import User, Wallet, WalletPayload, WalletRead, WalletReadNested, WalletUpdate

router = APIRouter(prefix="/wallets", tags=["wallets"])


def _wallet_owned(session: Session, wallet_id: int, owner_id: int) -> Wallet:
    w = session.get(Wallet, wallet_id)
    if not w or w.user_id != owner_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    return w


@router.get("", response_model=list[WalletRead])
def list_my_wallets(
    session: Annotated[Session, Depends(get_session)],
    current: Annotated[User, Depends(get_current_user)],
) -> list[Wallet]:
    stmt = select(Wallet).where(Wallet.user_id == current.id)
    return list(session.exec(stmt).all())


@router.get("/{wallet_id}", response_model=WalletReadNested)
def get_wallet(
    wallet_id: int,
    session: Annotated[Session, Depends(get_session)],
    current: Annotated[User, Depends(get_current_user)],
) -> Wallet:
    stmt = (
        select(Wallet)
        .where(Wallet.id == wallet_id, Wallet.user_id == current.id)
        .options(selectinload(Wallet.owner))
    )
    w = session.exec(stmt).first()
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    return w


@router.post("", response_model=WalletRead, status_code=status.HTTP_201_CREATED)
def create_wallet(
    body: WalletPayload,
    session: Annotated[Session, Depends(get_session)],
    current: Annotated[User, Depends(get_current_user)],
) -> Wallet:
    w = Wallet(user_id=current.id, **body.model_dump())
    session.add(w)
    session.commit()
    session.refresh(w)
    return w


@router.patch("/{wallet_id}", response_model=WalletRead)
def update_wallet(
    wallet_id: int,
    body: WalletUpdate,
    session: Annotated[Session, Depends(get_session)],
    current: Annotated[User, Depends(get_current_user)],
) -> Wallet:
    w = _wallet_owned(session, wallet_id, current.id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(w, k, v)
    session.add(w)
    session.commit()
    session.refresh(w)
    return w


@router.delete("/{wallet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wallet(
    wallet_id: int,
    session: Annotated[Session, Depends(get_session)],
    current: Annotated[User, Depends(get_current_user)],
) -> Response:
    w = _wallet_owned(session, wallet_id, current.id)
    if w.transactions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wallet still has transactions",
        )
    session.delete(w)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
