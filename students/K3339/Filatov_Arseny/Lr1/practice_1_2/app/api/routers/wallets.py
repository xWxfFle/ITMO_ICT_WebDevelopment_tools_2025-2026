from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.api.deps import get_session
from app.models import User, Wallet, WalletCreate, WalletRead, WalletReadNested, WalletUpdate

router = APIRouter(prefix="/wallets", tags=["wallets"])


def _wallet_or_404(session: Session, wallet_id: int) -> Wallet:
    w = session.get(Wallet, wallet_id)
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    return w


def _ensure_user(session: Session, user_id: int | None) -> None:
    if user_id is None or session.get(User, user_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user")


@router.get("", response_model=list[WalletRead])
def list_wallets(session: Session = Depends(get_session)) -> list[Wallet]:
    return list(session.exec(select(Wallet)).all())


@router.get("/{wallet_id}", response_model=WalletReadNested)
def get_wallet(wallet_id: int, session: Session = Depends(get_session)) -> Wallet:
    stmt = select(Wallet).where(Wallet.id == wallet_id).options(selectinload(Wallet.owner))
    w = session.exec(stmt).first()
    if not w:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wallet not found")
    return w


@router.post("", response_model=WalletRead, status_code=status.HTTP_201_CREATED)
def create_wallet(body: WalletCreate, session: Session = Depends(get_session)) -> Wallet:
    _ensure_user(session, body.user_id)
    w = Wallet.model_validate(body)
    session.add(w)
    session.commit()
    session.refresh(w)
    return w


@router.patch("/{wallet_id}", response_model=WalletRead)
def update_wallet(wallet_id: int, body: WalletUpdate, session: Session = Depends(get_session)) -> Wallet:
    w = _wallet_or_404(session, wallet_id)
    data = body.model_dump(exclude_unset=True)
    if "user_id" in data:
        _ensure_user(session, data["user_id"])
    for k, v in data.items():
        setattr(w, k, v)
    session.add(w)
    session.commit()
    session.refresh(w)
    return w


@router.delete("/{wallet_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_wallet(wallet_id: int, session: Session = Depends(get_session)) -> Response:
    w = _wallet_or_404(session, wallet_id)
    if w.transactions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wallet still has transactions",
        )
    session.delete(w)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
