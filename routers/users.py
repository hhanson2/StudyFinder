from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from auth_dependencies import get_current_user
from database import get_db
from models import (
    DiscussionPost,
    StudyGroup,
    StudyGroupMember,
    StudySession,
    User,
)
from schemas import UserResponse, UserUpdate

router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.put(
    "/me",
    response_model=UserResponse,
)
def update_current_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    display_name = user_data.display_name.strip()

    if not display_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Display name is required.",
        )

    current_user.display_name = display_name

    current_user.major = (
        user_data.major.strip()
        if user_data.major
        else None
    )

    current_user.school_year = (
        user_data.school_year.strip()
        if user_data.school_year
        else None
    )

    db.commit()
    db.refresh(current_user)

    return current_user


@router.get("/me/study-groups")
def get_current_user_study_groups(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.id

    member_group_ids = select(
        StudyGroupMember.group_id
    ).where(
        StudyGroupMember.user_id == user_id
    )

    groups = (
        db.query(
            StudyGroup.id,
            StudyGroup.group_name,
            StudyGroup.course_code,
            StudyGroup.description,
            StudyGroup.creator_user_id,
            StudyGroup.status,
            StudyGroup.max_members,
            StudyGroup.created_at,
            func.count(
                StudyGroupMember.user_id
            ).label("member_count"),
        )
        .outerjoin(
            StudyGroupMember,
            StudyGroup.id == StudyGroupMember.group_id,
        )
        .filter(
            or_(
                StudyGroup.creator_user_id == user_id,
                StudyGroup.id.in_(member_group_ids),
            )
        )
        .group_by(
            StudyGroup.id,
            StudyGroup.group_name,
            StudyGroup.course_code,
            StudyGroup.description,
            StudyGroup.creator_user_id,
            StudyGroup.status,
            StudyGroup.max_members,
            StudyGroup.created_at,
        )
        .order_by(StudyGroup.created_at.desc())
        .all()
    )

    return [
        {
            "id": group.id,
            "group_name": group.group_name,
            "course_code": group.course_code,
            "description": group.description,
            "creator_user_id": group.creator_user_id,
            "status": group.status,
            "max_members": group.max_members,
            "member_count": group.member_count,
            "created_at": group.created_at,
            "is_creator": (
                group.creator_user_id == user_id
            ),
        }
        for group in groups
    ]


@router.get("/me/sessions")
def get_current_user_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.id

    member_group_ids = select(
        StudyGroupMember.group_id
    ).where(
        StudyGroupMember.user_id == user_id
    )

    sessions = (
        db.query(
            StudySession.id,
            StudySession.title,
            StudySession.location,
            StudySession.meeting_link,
            StudySession.scheduled_at,
            StudySession.duration_minutes,
            StudyGroup.id.label("group_id"),
            StudyGroup.group_name,
            StudyGroup.course_code,
            StudyGroup.creator_user_id,
        )
        .join(
            StudyGroup,
            StudySession.group_id == StudyGroup.id,
        )
        .filter(
            or_(
                StudyGroup.creator_user_id == user_id,
                StudyGroup.id.in_(member_group_ids),
            )
        )
        .order_by(StudySession.scheduled_at)
        .all()
    )

    return [
        {
            "id": study_session.id,
            "title": study_session.title,
            "location": study_session.location,
            "meeting_link": study_session.meeting_link,
            "scheduled_at": study_session.scheduled_at,
            "duration_minutes": study_session.duration_minutes,
            "group_id": study_session.group_id,
            "group_name": study_session.group_name,
            "course_code": study_session.course_code,
            "can_manage": (
                study_session.creator_user_id == user_id
            ),
        }
        for study_session in sessions
    ]


@router.get("/me/profile")
def get_current_user_profile_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.id

    member_group_ids = select(
        StudyGroupMember.group_id
    ).where(
        StudyGroupMember.user_id == user_id
    )

    groups_created = (
        db.query(func.count(StudyGroup.id))
        .filter(
            StudyGroup.creator_user_id == user_id
        )
        .scalar()
    ) or 0

    groups_joined = (
        db.query(
            func.count(StudyGroupMember.group_id)
        )
        .filter(
            StudyGroupMember.user_id == user_id
        )
        .scalar()
    ) or 0

    upcoming_sessions = (
        db.query(func.count(StudySession.id))
        .join(
            StudyGroup,
            StudySession.group_id == StudyGroup.id,
        )
        .filter(
            or_(
                StudyGroup.creator_user_id == user_id,
                StudyGroup.id.in_(member_group_ids),
            ),
            StudySession.scheduled_at >= datetime.now(),
        )
        .scalar()
    ) or 0

    discussion_posts = (
        db.query(func.count(DiscussionPost.id))
        .filter(
            DiscussionPost.user_id == user_id
        )
        .scalar()
    ) or 0

    return {
        "user": {
            "id": current_user.id,
            "display_name": current_user.display_name,
            "email": current_user.email,
            "major": current_user.major,
            "school_year": current_user.school_year,
            "created_at": current_user.created_at,
        },
        "stats": {
            "groups_created": groups_created,
            "groups_joined": groups_joined,
            "upcoming_sessions": upcoming_sessions,
            "discussion_posts": discussion_posts,
        },
    }