from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import StudyGroup, User
from schemas import StudyGroupCreate, StudyGroupResponse, StudyGroupUpdate

router = APIRouter()


@router.post(
    "/",
    response_model=StudyGroupResponse,
    status_code=status.HTTP_201_CREATED
)
def create_study_group(
    group_data: StudyGroupCreate,
    db: Session = Depends(get_db)
):
    creator = (
        db.query(User)
        .filter(User.id == group_data.creator_user_id)
        .first()
    )

    if not creator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Creator user not found."
        )

    if group_data.max_members <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum members must be greater than zero."
        )

    new_group = StudyGroup(
        group_name=group_data.group_name,
        course_code=group_data.course_code.upper(),
        description=group_data.description,
        creator_user_id=group_data.creator_user_id,
        status=group_data.status,
        max_members=group_data.max_members
    )

    db.add(new_group)
    db.commit()
    db.refresh(new_group)

    return new_group


@router.get("/", response_model=list[StudyGroupResponse])
def get_study_groups(
    course_code: str | None = Query(default=None),
    db: Session = Depends(get_db)
):
    query = db.query(StudyGroup)

    if course_code:
        query = query.filter(
            StudyGroup.course_code.ilike(f"%{course_code}%")
        )

    return query.order_by(StudyGroup.id).all()


@router.get("/{group_id}", response_model=StudyGroupResponse)
def get_study_group(
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

    return group


@router.put("/{group_id}", response_model=StudyGroupResponse)
def update_study_group(
    group_id: int,
    group_data: StudyGroupUpdate,
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

    if group_data.max_members <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum members must be greater than zero."
        )

    group.group_name = group_data.group_name
    group.course_code = group_data.course_code.upper()
    group.description = group_data.description
    group.status = group_data.status
    group.max_members = group_data.max_members

    db.commit()
    db.refresh(group)

    return group


@router.delete(
    "/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_study_group(
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

    db.delete(group)
    db.commit()

    return None