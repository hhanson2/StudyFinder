from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session

from auth_dependencies import get_current_user
from database import get_db
from models import (
    DiscussionPost,
    DiscussionReply,
    StudyGroup,
    StudyGroupMember,
    User,
)
from schemas import (
    DiscussionPostCreate,
    DiscussionPostResponse,
    DiscussionPostUpdate,
    DiscussionReplyCreate,
    DiscussionReplyResponse,
    DiscussionReplyUpdate,
)

router = APIRouter()


def get_group_or_404(
    group_id: int,
    db: Session,
) -> StudyGroup:
    group = (
        db.query(StudyGroup)
        .filter(StudyGroup.id == group_id)
        .first()
    )

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study group not found.",
        )

    return group


def get_post_or_404(
    post_id: int,
    db: Session,
) -> DiscussionPost:
    post = (
        db.query(DiscussionPost)
        .filter(DiscussionPost.id == post_id)
        .first()
    )

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discussion post not found.",
        )

    return post


def get_reply_or_404(
    reply_id: int,
    db: Session,
) -> DiscussionReply:
    reply = (
        db.query(DiscussionReply)
        .filter(DiscussionReply.id == reply_id)
        .first()
    )

    if not reply:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Discussion reply not found.",
        )

    return reply


def require_group_member(
    group: StudyGroup,
    current_user: User,
    db: Session,
):
    if group.creator_user_id == current_user.id:
        return

    membership = (
        db.query(StudyGroupMember)
        .filter(
            StudyGroupMember.group_id == group.id,
            StudyGroupMember.user_id == current_user.id,
        )
        .first()
    )

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Only group members can access "
                "this discussion."
            ),
        )


def serialize_post(
    post: DiscussionPost,
    display_name: str,
):
    return {
        "id": post.id,
        "group_id": post.group_id,
        "user_id": post.user_id,
        "display_name": display_name,
        "title": post.title,
        "content": post.content,
        "created_at": post.created_at,
    }


def serialize_reply(
    reply: DiscussionReply,
    display_name: str,
):
    return {
        "id": reply.id,
        "post_id": reply.post_id,
        "user_id": reply.user_id,
        "display_name": display_name,
        "content": reply.content,
        "created_at": reply.created_at,
    }


@router.post(
    "/study-groups/{group_id}/posts",
    response_model=DiscussionPostResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_discussion_post(
    group_id: int,
    post_data: DiscussionPostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = get_group_or_404(group_id, db)

    require_group_member(
        group,
        current_user,
        db,
    )

    title = post_data.title.strip()
    content = post_data.content.strip()

    if not title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Post title is required.",
        )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Post content is required.",
        )

    new_post = DiscussionPost(
        group_id=group_id,
        user_id=current_user.id,
        title=title,
        content=content,
    )

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return serialize_post(
        new_post,
        current_user.display_name,
    )


@router.get(
    "/study-groups/{group_id}/posts",
    response_model=list[DiscussionPostResponse],
)
def get_group_posts(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = get_group_or_404(group_id, db)

    require_group_member(
        group,
        current_user,
        db,
    )

    results = (
        db.query(
            DiscussionPost,
            User.display_name,
        )
        .join(
            User,
            DiscussionPost.user_id == User.id,
        )
        .filter(
            DiscussionPost.group_id == group_id
        )
        .order_by(
            DiscussionPost.created_at.desc()
        )
        .all()
    )

    return [
        serialize_post(post, display_name)
        for post, display_name in results
    ]


@router.get(
    "/posts/{post_id}",
    response_model=DiscussionPostResponse,
)
def get_discussion_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = get_post_or_404(post_id, db)
    group = get_group_or_404(post.group_id, db)

    require_group_member(
        group,
        current_user,
        db,
    )

    author = (
        db.query(User)
        .filter(User.id == post.user_id)
        .first()
    )

    return serialize_post(
        post,
        author.display_name,
    )


@router.put(
    "/posts/{post_id}",
    response_model=DiscussionPostResponse,
)
def update_discussion_post(
    post_id: int,
    post_data: DiscussionPostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = get_post_or_404(post_id, db)
    group = get_group_or_404(post.group_id, db)

    require_group_member(
        group,
        current_user,
        db,
    )

    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own posts.",
        )

    title = post_data.title.strip()
    content = post_data.content.strip()

    if not title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Post title is required.",
        )

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Post content is required.",
        )

    post.title = title
    post.content = content

    db.commit()
    db.refresh(post)

    return serialize_post(
        post,
        current_user.display_name,
    )


@router.delete(
    "/posts/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_discussion_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = get_post_or_404(post_id, db)
    group = get_group_or_404(post.group_id, db)

    require_group_member(
        group,
        current_user,
        db,
    )

    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own posts.",
        )

    db.delete(post)
    db.commit()

    return None


@router.post(
    "/posts/{post_id}/replies",
    response_model=DiscussionReplyResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_discussion_reply(
    post_id: int,
    reply_data: DiscussionReplyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = get_post_or_404(post_id, db)
    group = get_group_or_404(post.group_id, db)

    require_group_member(
        group,
        current_user,
        db,
    )

    content = reply_data.content.strip()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reply content is required.",
        )

    new_reply = DiscussionReply(
        post_id=post_id,
        user_id=current_user.id,
        content=content,
    )

    db.add(new_reply)
    db.commit()
    db.refresh(new_reply)

    return serialize_reply(
        new_reply,
        current_user.display_name,
    )


@router.get(
    "/posts/{post_id}/replies",
    response_model=list[DiscussionReplyResponse],
)
def get_discussion_replies(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    post = get_post_or_404(post_id, db)
    group = get_group_or_404(post.group_id, db)

    require_group_member(
        group,
        current_user,
        db,
    )

    results = (
        db.query(
            DiscussionReply,
            User.display_name,
        )
        .join(
            User,
            DiscussionReply.user_id == User.id,
        )
        .filter(
            DiscussionReply.post_id == post_id
        )
        .order_by(
            DiscussionReply.created_at
        )
        .all()
    )

    return [
        serialize_reply(reply, display_name)
        for reply, display_name in results
    ]


@router.put(
    "/replies/{reply_id}",
    response_model=DiscussionReplyResponse,
)
def update_discussion_reply(
    reply_id: int,
    reply_data: DiscussionReplyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reply = get_reply_or_404(reply_id, db)
    post = get_post_or_404(reply.post_id, db)
    group = get_group_or_404(post.group_id, db)

    require_group_member(
        group,
        current_user,
        db,
    )

    if reply.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own replies.",
        )

    content = reply_data.content.strip()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reply content is required.",
        )

    reply.content = content

    db.commit()
    db.refresh(reply)

    return serialize_reply(
        reply,
        current_user.display_name,
    )


@router.delete(
    "/replies/{reply_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_discussion_reply(
    reply_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    reply = get_reply_or_404(reply_id, db)
    post = get_post_or_404(reply.post_id, db)
    group = get_group_or_404(post.group_id, db)

    require_group_member(
        group,
        current_user,
        db,
    )

    if reply.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own replies.",
        )

    db.delete(reply)
    db.commit()

    return None