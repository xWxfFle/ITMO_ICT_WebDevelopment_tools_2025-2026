from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.api.deps import get_current_user
from app.core.security import hash_password, verify_password
from app.db.session import get_session
from app.models import PasswordChange, User, UserRead, UserReadNested, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def read_me(current: Annotated[User, Depends(get_current_user)]) -> User:
    return current


@router.patch("/me/password", response_model=UserRead)
def change_password(
    body: PasswordChange,
    session: Annotated[Session, Depends(get_session)],
    current: Annotated[User, Depends(get_current_user)],
) -> User:
    if not verify_password(body.current_password, current.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is wrong")
    current.password_hash = hash_password(body.new_password)
    session.add(current)
    session.commit()
    session.refresh(current)
    return current


@router.get("", response_model=list[UserRead])
def list_users(
    session: Annotated[Session, Depends(get_session)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[User]:
    return list(session.exec(select(User)).all())


@router.get("/{user_id}", response_model=UserReadNested)
def get_user(
    user_id: int,
    session: Annotated[Session, Depends(get_session)],
    _: Annotated[User, Depends(get_current_user)],
) -> User:
    stmt = (
        select(User)
        .where(User.id == user_id)
        .options(selectinload(User.wallets), selectinload(User.categories))
    )
    user = session.exec(stmt).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserRead)
def update_profile(
    user_id: int,
    body: UserUpdate,
    session: Annotated[Session, Depends(get_session)],
    current: Annotated[User, Depends(get_current_user)],
) -> User:
    if user_id != current.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only edit your own profile")
    data = body.model_dump(exclude_unset=True)
    if "email" in data and data["email"] != current.email:
        dup = session.exec(select(User).where(User.email == data["email"])).first()
        if dup:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    for k, v in data.items():
        setattr(current, k, v)
    session.add(current)
    session.commit()
    session.refresh(current)
    return current


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_account(
    user_id: int,
    session: Annotated[Session, Depends(get_session)],
    current: Annotated[User, Depends(get_current_user)],
) -> Response:
    if user_id != current.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only delete your own account")
    if current.wallets or current.categories or current.transactions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Remove wallets, categories and transactions first",
        )
    session.delete(current)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
