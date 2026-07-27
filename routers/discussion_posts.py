from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import DiscussionPost, Notification, StudyGroup, StudyGroupMember, User
from schemas import DiscussionPostCreate, DiscussionPostResponse

router = APIRouter()


def _serialize_post(post: DiscussionPost, author_name: str) -> dict:
    return {
        "id": post.id,
        "group_id": post.group_id,
        "user_id": post.user_id,
        "author_name": author_name,
        "parent_post_id": post.parent_post_id,
        "title": post.title,
        "content": post.content,
        "created_at": post.created_at,
    }


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

    if post_data.parent_post_id is not None:
        parent_post = (
            db.query(DiscussionPost)
            .filter(
                DiscussionPost.id == post_data.parent_post_id,
                DiscussionPost.group_id == group_id
            )
            .first()
        )

        if not parent_post:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="The post you're replying to was not found in this group."
            )

    new_post = DiscussionPost(
        group_id=group_id,
        user_id=post_data.user_id,
        parent_post_id=post_data.parent_post_id,
        title=post_data.title,
        content=post_data.content
    )

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    member_ids = (
        db.query(StudyGroupMember.user_id)
        .filter(StudyGroupMember.group_id == group_id)
        .all()
    )

    notify_user_ids = {row.user_id for row in member_ids}
    notify_user_ids.add(group.creator_user_id)
    notify_user_ids.discard(post_data.user_id)

    for member_id in notify_user_ids:
        db.add(
            Notification(
                user_id=member_id,
                message=f"New discussion reply in {group.group_name}"
            )
        )

    db.commit()

    return _serialize_post(new_post, user.display_name)


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

    rows = (
        db.query(DiscussionPost, User.display_name)
        .join(User, DiscussionPost.user_id == User.id)
        .filter(DiscussionPost.group_id == group_id)
        .order_by(DiscussionPost.created_at.asc())
        .all()
    )

    return [_serialize_post(post, author_name) for post, author_name in rows]


@router.get(
    "/posts/{post_id}",
    response_model=DiscussionPostResponse
)
def get_discussion_post(
    post_id: int,
    db: Session = Depends(get_db)
):
    row = (
        db.query(DiscussionPost, User.display_name)
        .join(User, DiscussionPost.user_id == User.id)
        .filter(DiscussionPost.id == post_id)
        .first()
    )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discussion post not found."
        )

    post, author_name = row
    return _serialize_post(post, author_name)


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
