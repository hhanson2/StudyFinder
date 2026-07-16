from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import DiscussionPost, StudyGroup, User
from schemas import DiscussionPostCreate, DiscussionPostResponse

router = APIRouter()


@router.post(
    "/study-groups/{group_id}/posts",
    response_model=DiscussionPostResponse,
    status_code=status.HTTP_201_CREATED
)
def create_discussion_post(
    group_id: int,
    post_data: DiscussionPostCreate,
    db: Session = Depends(get_db)
):
    group = (
        db.query(StudyGroup)
        .filter(StudyGroup.id == group_id)
        .first()
    )

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study group not found."
        )

    user = (
        db.query(User)
        .filter(User.id == post_data.user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    new_post = DiscussionPost(
        group_id=group_id,
        user_id=post_data.user_id,
        title=post_data.title,
        content=post_data.content
    )

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post


@router.get(
    "/study-groups/{group_id}/posts",
    response_model=list[DiscussionPostResponse]
)
def get_group_posts(
    group_id: int,
    db: Session = Depends(get_db)
):
    group = (
        db.query(StudyGroup)
        .filter(StudyGroup.id == group_id)
        .first()
    )

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study group not found."
        )

    return (
        db.query(DiscussionPost)
        .filter(DiscussionPost.group_id == group_id)
        .order_by(DiscussionPost.created_at.desc())
        .all()
    )


@router.get(
    "/posts/{post_id}",
    response_model=DiscussionPostResponse
)
def get_discussion_post(
    post_id: int,
    db: Session = Depends(get_db)
):
    post = (
        db.query(DiscussionPost)
        .filter(DiscussionPost.id == post_id)
        .first()
    )

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discussion post not found."
        )

    return post


@router.delete(
    "/posts/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_discussion_post(
    post_id: int,
    db: Session = Depends(get_db)
):
    post = (
        db.query(DiscussionPost)
        .filter(DiscussionPost.id == post_id)
        .first()
    )

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discussion post not found."
        )

    db.delete(post)
    db.commit()

    return None