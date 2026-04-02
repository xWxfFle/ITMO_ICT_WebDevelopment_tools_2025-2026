from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.api.deps import get_session
from app.models import (
    User,
    UserCreate,
    UserRead,
    UserReadNested,
    UserUpdate,
)

router = APIRouter(prefix="/users", tags=["users"])


def _get_user_or_404(session: Session, user_id: int) -> User:
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("", response_model=list[UserRead])
def list_users(session: Session = Depends(get_session)) -> list[User]:
    return list(session.exec(select(User)).all())


@router.get("/{user_id}", response_model=UserReadNested)
def get_user(user_id: int, session: Session = Depends(get_session)) -> User:
    stmt = (
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.wallets), selectinload(User.categories))
    )
    user = session.exec(stmt).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(body: UserCreate, session: Session = Depends(get_session)) -> User:
    dup = session.exec(select(User).where(User.email == body.email)).first()
    if dup:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    u = User.model_validate(body)
    session.add(u)
    session.commit()
    session.refresh(u)
    return u


@router.patch("/{user_id}", response_model=UserRead)
def update_user(user_id: int, body: UserUpdate, session: Session = Depends(get_session)) -> User:
    u = _get_user_or_404(session, user_id)
    data = body.model_dump(exclude_unset=True)
    if "email" in data and data["email"] != u.email:
        dup = session.exec(select(User).where(User.email == data["email"])).first()
        if dup:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    for k, v in data.items():
        setattr(u, k, v)
    session.add(u)
    session.commit()
    session.refresh(u)
    return u


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, session: Session = Depends(get_session)) -> Response:
    u = _get_user_or_404(session, user_id)
    if u.wallets or u.categories or u.transactions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User still has wallets, categories or transactions",
        )
    session.delete(u)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
