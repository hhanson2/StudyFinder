from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from database import get_db
from models import (
    Notification,
    StudyGroup,
    StudyGroupMember,
    StudySession,
    User
)

router = APIRouter()


@router.get("/{user_id}")
def get_dashboard(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    member_group_ids = (
        db.query(StudyGroupMember.group_id)
        .filter(StudyGroupMember.user_id == user_id)
    )

    my_groups = (
        db.query(
            StudyGroup.id,
            StudyGroup.group_name,
            StudyGroup.course_code,
            StudyGroup.description,
            StudyGroup.status,
            StudyGroup.max_members,
            func.count(StudyGroupMember.user_id).label("member_count")
        )
        .outerjoin(
            StudyGroupMember,
            StudyGroup.id == StudyGroupMember.group_id
        )
        .filter(
            or_(
                StudyGroup.creator_user_id == user_id,
                StudyGroup.id.in_(member_group_ids)
            )
        )
        .group_by(StudyGroup.id)
        .order_by(StudyGroup.created_at.desc())
        .all()
    )

    popular_groups = (
        db.query(
            StudyGroup.id,
            StudyGroup.group_name,
            StudyGroup.course_code,
            StudyGroup.description,
            StudyGroup.status,
            StudyGroup.max_members,
            func.count(StudyGroupMember.user_id).label("member_count")
        )
        .outerjoin(
            StudyGroupMember,
            StudyGroup.id == StudyGroupMember.group_id
        )
        .filter(StudyGroup.status == "open")
        .group_by(StudyGroup.id)
        .order_by(func.count(StudyGroupMember.user_id).desc())
        .limit(5)
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
            StudyGroup.course_code
        )
        .join(StudyGroup, StudySession.group_id == StudyGroup.id)
        .filter(
            or_(
                StudyGroup.creator_user_id == user_id,
                StudyGroup.id.in_(member_group_ids)
            ),
            StudySession.scheduled_at >= datetime.now()
        )
        .order_by(StudySession.scheduled_at)
        .limit(5)
        .all()
    )

    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(5)
        .all()
    )

    return {
        "user": {
            "id": user.id,
            "display_name": user.display_name,
            "email": user.email,
            "major": user.major,
            "school_year": user.school_year
        },
        "my_groups": [
            {
                "id": group.id,
                "group_name": group.group_name,
                "course_code": group.course_code,
                "description": group.description,
                "status": group.status,
                "max_members": group.max_members,
                "member_count": group.member_count
            }
            for group in my_groups
        ],
        "popular_groups": [
            {
                "id": group.id,
                "group_name": group.group_name,
                "course_code": group.course_code,
                "description": group.description,
                "status": group.status,
                "max_members": group.max_members,
                "member_count": group.member_count
            }
            for group in popular_groups
        ],
        "upcoming_sessions": [
            {
                "id": session.id,
                "title": session.title,
                "location": session.location,
                "meeting_link": session.meeting_link,
                "scheduled_at": session.scheduled_at,
                "duration_minutes": session.duration_minutes,
                "group_id": session.group_id,
                "group_name": session.group_name,
                "course_code": session.course_code
            }
            for session in upcoming_sessions
        ],
        "notifications": [
            {
                "id": notification.id,
                "message": notification.message,
                "is_read": notification.is_read,
                "created_at": notification.created_at
            }
            for notification in notifications
        ]
    }