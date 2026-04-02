from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.api.deps import get_current_user
from app.db.session import get_session
from app.models import Category, CategoryPayload, CategoryRead, CategoryReadNested, CategoryUpdate, User

router = APIRouter(prefix="/categories", tags=["categories"])


def _category_owned(session: Session, category_id: int, owner_id: int) -> Category:
    c = session.get(Category, category_id)
    if not c or c.user_id != owner_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return c


@router.get("", response_model=list[CategoryRead])
def list_my_categories(
    session: Annotated[Session, Depends(get_session)],
    current: Annotated[User, Depends(get_current_user)],
) -> list[Category]:
    stmt = select(Category).where(Category.user_id == current.id)
    return list(session.exec(stmt).all())


@router.get("/{category_id}", response_model=CategoryReadNested)
def get_category(
    category_id: int,
    session: Annotated[Session, Depends(get_session)],
    current: Annotated[User, Depends(get_current_user)],
) -> Category:
    stmt = (
        select(Category)
        .where(Category.id == category_id, Category.user_id == current.id)
        .options(selectinload(Category.owner))
    )
    c = session.exec(stmt).first()
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return c


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    body: CategoryPayload,
    session: Annotated[Session, Depends(get_session)],
    current: Annotated[User, Depends(get_current_user)],
) -> Category:
    c = Category(user_id=current.id, **body.model_dump())
    session.add(c)
    session.commit()
    session.refresh(c)
    return c


@router.patch("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: int,
    body: CategoryUpdate,
    session: Annotated[Session, Depends(get_session)],
    current: Annotated[User, Depends(get_current_user)],
) -> Category:
    c = _category_owned(session, category_id, current.id)
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    session.add(c)
    session.commit()
    session.refresh(c)
    return c


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    session: Annotated[Session, Depends(get_session)],
    current: Annotated[User, Depends(get_current_user)],
) -> Response:
    c = _category_owned(session, category_id, current.id)
    if c.transactions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category still has transactions",
        )
    session.delete(c)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
