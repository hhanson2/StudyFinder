from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from schemas import UserCreate, UserResponse
from database import get_db
from models import DiscussionPost, StudyGroup, StudyGroupMember, StudySession, User
from datetime import datetime

router = APIRouter()


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    existing_user = (
        db.query(User)
        .filter(User.email == str(user_data.email))
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists."
        )

    new_user = User(
        display_name=user_data.display_name,
        email=str(user_data.email),
        major=user_data.major,
        school_year=user_data.school_year
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.get("/", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id).all()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
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

    return user


@router.get("/{user_id}/study-groups")
def get_user_study_groups(
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

    groups = (
        db.query(
            StudyGroup.id,
            StudyGroup.group_name,
            StudyGroup.course_code,
            StudyGroup.description,
            StudyGroup.status,
            StudyGroup.max_members,
            StudyGroup.created_at,
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

    return [
        {
            "id": group.id,
            "group_name": group.group_name,
            "course_code": group.course_code,
            "description": group.description,
            "status": group.status,
            "max_members": group.max_members,
            "member_count": group.member_count,
            "created_at": group.created_at
        }
        for group in groups
    ]



@router.get("/{user_id}/sessions")
def get_user_sessions(
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
        .all()
    )

    return [
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
        for session in sessions
    ]


@router.get("/{user_id}/profile")
def get_user_profile(
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

    groups_created = (
        db.query(func.count(StudyGroup.id))
        .filter(StudyGroup.creator_user_id == user_id)
        .scalar()
    )

    groups_joined = (
        db.query(func.count(StudyGroupMember.group_id))
        .filter(StudyGroupMember.user_id == user_id)
        .scalar()
    )

    member_group_ids = (
        db.query(StudyGroupMember.group_id)
        .filter(StudyGroupMember.user_id == user_id)
    )

    upcoming_sessions = (
        db.query(func.count(StudySession.id))
        .join(StudyGroup, StudySession.group_id == StudyGroup.id)
        .filter(
            or_(
                StudyGroup.creator_user_id == user_id,
                StudyGroup.id.in_(member_group_ids)
            ),
            StudySession.scheduled_at >= datetime.now()
        )
        .scalar()
    )

    discussion_posts = (
        db.query(func.count(DiscussionPost.id))
        .filter(DiscussionPost.user_id == user_id)
        .scalar()
    )

    return {
        "user": {
            "id": user.id,
            "display_name": user.display_name,
            "email": user.email,
            "major": user.major,
            "school_year": user.school_year,
            "created_at": user.created_at
        },
        "stats": {
            "groups_created": groups_created,
            "groups_joined": groups_joined,
            "upcoming_sessions": upcoming_sessions,
            "discussion_posts": discussion_posts
        }
    }