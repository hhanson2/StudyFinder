from datetime import datetime

from fastapi import APIRouter, Depends
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

router = APIRouter()


@router.get("/")
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_id = current_user.id

    member_group_ids = select(
        StudyGroupMember.group_id
    ).where(
        StudyGroupMember.user_id == user_id
    )

    joined_group_count = (
        db.query(func.count(StudyGroupMember.group_id))
        .filter(StudyGroupMember.user_id == user_id)
        .scalar()
    ) or 0

    created_group_count = (
        db.query(func.count(StudyGroup.id))
        .filter(StudyGroup.creator_user_id == user_id)
        .scalar()
    ) or 0

    upcoming_session_count = (
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

    discussion_post_count = (
        db.query(func.count(DiscussionPost.id))
        .filter(DiscussionPost.user_id == user_id)
        .scalar()
    ) or 0

    my_groups = (
        db.query(
            StudyGroup.id,
            StudyGroup.group_name,
            StudyGroup.course_code,
            StudyGroup.description,
            StudyGroup.status,
            StudyGroup.max_members,
            StudyGroup.creator_user_id,
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
            StudyGroup.status,
            StudyGroup.max_members,
            StudyGroup.creator_user_id,
            StudyGroup.created_at,
        )
        .order_by(StudyGroup.created_at.desc())
        .all()
    )

    upcoming_sessions = (
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
        )
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
        .order_by(StudySession.scheduled_at)
        .limit(5)
        .all()
    )


    return {
        "user": {
            "id": current_user.id,
            "display_name": current_user.display_name,
            "email": current_user.email,
            "major": current_user.major,
            "school_year": current_user.school_year,
        },
        "summary": {
            "joined_groups": joined_group_count,
            "created_groups": created_group_count,
            "upcoming_sessions": upcoming_session_count,
            "discussion_posts": discussion_post_count,
        },
        "my_groups": [
            {
                "id": group.id,
                "group_name": group.group_name,
                "course_code": group.course_code,
                "description": group.description,
                "status": group.status,
                "max_members": group.max_members,
                "creator_user_id": group.creator_user_id,
                "member_count": group.member_count,
                "created_at": group.created_at,
            }
            for group in my_groups
        ],
        "upcoming_sessions": [
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
                
            }
            for study_session in upcoming_sessions
        ],
        
    }