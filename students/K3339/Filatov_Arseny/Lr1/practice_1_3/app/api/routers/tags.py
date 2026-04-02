from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlmodel import Session, select

from app.api.deps import get_current_user
from app.db.session import get_session
from app.models import Tag, TagCreate, TagRead, TagUpdate, User

router = APIRouter(prefix="/tags", tags=["tags"])


def _tag_or_404(session: Session, tag_id: int) -> Tag:
    t = session.get(Tag, tag_id)
    if not t:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    return t


@router.get("", response_model=list[TagRead])
def list_tags(
    session: Annotated[Session, Depends(get_session)],
    _: Annotated[User, Depends(get_current_user)],
) -> list[Tag]:
    return list(session.exec(select(Tag)).all())


@router.get("/{tag_id}", response_model=TagRead)
def get_tag(
    tag_id: int,
    session: Annotated[Session, Depends(get_session)],
    _: Annotated[User, Depends(get_current_user)],
) -> Tag:
    return _tag_or_404(session, tag_id)


@router.post("", response_model=TagRead, status_code=status.HTTP_201_CREATED)
def create_tag(
    body: TagCreate,
    session: Annotated[Session, Depends(get_session)],
    _: Annotated[User, Depends(get_current_user)],
) -> Tag:
    dup = session.exec(select(Tag).where(Tag.name == body.name)).first()
    if dup:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tag name taken")
    t = Tag.model_validate(body)
    session.add(t)
    session.commit()
    session.refresh(t)
    return t


@router.patch("/{tag_id}", response_model=TagRead)
def update_tag(
    tag_id: int,
    body: TagUpdate,
    session: Annotated[Session, Depends(get_session)],
    _: Annotated[User, Depends(get_current_user)],
) -> Tag:
    t = _tag_or_404(session, tag_id)
    data = body.model_dump(exclude_unset=True)
    if "name" in data and data["name"] != t.name:
        dup = session.exec(select(Tag).where(Tag.name == data["name"])).first()
        if dup:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tag name taken")
    for k, v in data.items():
        setattr(t, k, v)
    session.add(t)
    session.commit()
    session.refresh(t)
    return t


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: int,
    session: Annotated[Session, Depends(get_session)],
    _: Annotated[User, Depends(get_current_user)],
) -> Response:
    t = _tag_or_404(session, tag_id)
    if t.transactions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag is still linked to transactions",
        )
    session.delete(t)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
