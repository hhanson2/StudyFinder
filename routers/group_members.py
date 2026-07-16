from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import StudyGroup, StudyGroupMember, User
from schemas import StudyGroupMemberResponse

router = APIRouter()


@router.post(
    "/{group_id}/members/{user_id}",
    status_code=status.HTTP_201_CREATED
)
def join_study_group(
    group_id: int,
    user_id: int,
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
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    existing_member = (
        db.query(StudyGroupMember)
        .filter(
            StudyGroupMember.group_id == group_id,
            StudyGroupMember.user_id == user_id
        )
        .first()
    )

    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this group."
        )

    member_count = (
        db.query(func.count(StudyGroupMember.user_id))
        .filter(StudyGroupMember.group_id == group_id)
        .scalar()
    )

    if member_count >= group.max_members:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This study group is full."
        )

    new_member = StudyGroupMember(
        group_id=group_id,
        user_id=user_id
    )

    db.add(new_member)
    db.commit()
    db.refresh(new_member)

    return {
        "group_id": group_id,
        "user_id": user_id,
        "message": "User joined the study group."
    }


@router.get(
    "/{group_id}/members",
    response_model=list[StudyGroupMemberResponse]
)
def get_group_members(
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

    members = (
        db.query(
            User.id.label("user_id"),
            User.display_name,
            User.email,
            StudyGroupMember.joined_at
        )
        .join(StudyGroupMember, User.id == StudyGroupMember.user_id)
        .filter(StudyGroupMember.group_id == group_id)
        .order_by(StudyGroupMember.joined_at)
        .all()
    )

    return members


@router.delete(
    "/{group_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def leave_study_group(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db)
):
    member = (
        db.query(StudyGroupMember)
        .filter(
            StudyGroupMember.group_id == group_id,
            StudyGroupMember.user_id == user_id
        )
        .first()
    )

    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of this group."
        )

    db.delete(member)
    db.commit()

    return None