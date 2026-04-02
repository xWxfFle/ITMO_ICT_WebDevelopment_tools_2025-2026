from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import selectinload
from sqlmodel import Session, select

from app.api.deps import get_session
from app.models import Category, CategoryCreate, CategoryRead, CategoryReadNested, CategoryUpdate, User

router = APIRouter(prefix="/categories", tags=["categories"])


def _category_or_404(session: Session, category_id: int) -> Category:
    c = session.get(Category, category_id)
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return c


def _ensure_user(session: Session, user_id: int | None) -> None:
    if user_id is None or session.get(User, user_id) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user")


@router.get("", response_model=list[CategoryRead])
def list_categories(session: Session = Depends(get_session)) -> list[Category]:
    return list(session.exec(select(Category)).all())


@router.get("/{category_id}", response_model=CategoryReadNested)
def get_category(category_id: int, session: Session = Depends(get_session)) -> Category:
    stmt = select(Category).where(Category.id == category_id).options(selectinload(Category.owner))
    c = session.exec(stmt).first()
    if not c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return c


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(body: CategoryCreate, session: Session = Depends(get_session)) -> Category:
    _ensure_user(session, body.user_id)
    c = Category.model_validate(body)
    session.add(c)
    session.commit()
    session.refresh(c)
    return c


@router.patch("/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: int,
    body: CategoryUpdate,
    session: Session = Depends(get_session),
) -> Category:
    c = _category_or_404(session, category_id)
    data = body.model_dump(exclude_unset=True)
    if "user_id" in data:
        _ensure_user(session, data["user_id"])
    for k, v in data.items():
        setattr(c, k, v)
    session.add(c)
    session.commit()
    session.refresh(c)
    return c


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, session: Session = Depends(get_session)) -> Response:
    c = _category_or_404(session, category_id)
    if c.transactions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category still has transactions",
        )
    session.delete(c)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
