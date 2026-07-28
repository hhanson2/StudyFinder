from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from auth_dependencies import get_current_user
from database import get_db
from models import (
    StudyGroup,
    StudyGroupMember,
    User,
)
from schemas import (
    StudyGroupCreate,
    StudyGroupResponse,
    StudyGroupUpdate,
)

router = APIRouter()


@router.post(
    "/",
    response_model=StudyGroupResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_study_group(
    group_data: StudyGroupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group_name = group_data.group_name.strip()
    course_code = group_data.course_code.strip().upper()

    if not group_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Group name is required.",
        )

    if not course_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course code is required.",
        )

    if group_data.max_members <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum members must be greater than zero.",
        )

    if group_data.status not in {"open", "closed"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be open or closed.",
        )

    new_group = StudyGroup(
        group_name=group_name,
        course_code=course_code,
        description=(
            group_data.description.strip()
            if group_data.description
            else None
        ),
        creator_user_id=current_user.id,
        status=group_data.status,
        max_members=group_data.max_members,
    )

    db.add(new_group)
    db.flush()

    creator_membership = StudyGroupMember(
        group_id=new_group.id,
        user_id=current_user.id,
    )

    db.add(creator_membership)
    db.commit()
    db.refresh(new_group)

    return new_group


@router.get(
    "/",
    response_model=list[StudyGroupResponse],
)
def get_study_groups(
    course_code: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(StudyGroup)

    if course_code:
        search_value = course_code.strip()

        query = query.filter(
            or_(
                StudyGroup.course_code.ilike(
                    f"%{search_value}%"
                ),
                StudyGroup.group_name.ilike(
                    f"%{search_value}%"
                ),
            )
        )

    return (
        query
        .order_by(StudyGroup.created_at.desc())
        .all()
    )


@router.get(
    "/{group_id}",
    response_model=StudyGroupResponse,
)
def get_study_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
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


@router.put(
    "/{group_id}",
    response_model=StudyGroupResponse,
)
def update_study_group(
    group_id: int,
    group_data: StudyGroupUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
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

    if group.creator_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the group creator can edit this group.",
        )

    group_name = group_data.group_name.strip()
    course_code = group_data.course_code.strip().upper()

    if not group_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Group name is required.",
        )

    if not course_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course code is required.",
        )

    if group_data.max_members <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum members must be greater than zero.",
        )

    if group_data.status not in {"open", "closed"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be open or closed.",
        )

    member_count = (
        db.query(
            func.count(StudyGroupMember.user_id)
        )
        .filter(
            StudyGroupMember.group_id == group_id
        )
        .scalar()
    ) or 0

    if group_data.max_members < member_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Maximum members cannot be lower "
                "than the current member count."
            ),
        )

    group.group_name = group_name
    group.course_code = course_code
    group.description = (
        group_data.description.strip()
        if group_data.description
        else None
    )
    group.status = group_data.status
    group.max_members = group_data.max_members

    db.commit()
    db.refresh(group)

    return group


@router.delete(
    "/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_study_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
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

    if group.creator_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the group creator can delete this group.",
        )

    db.delete(group)
    db.commit()

    return None