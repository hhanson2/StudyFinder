from datetime import datetime

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
    StudyGroup,
    StudyGroupMember,
    StudySession,
    User,
)
from schemas import (
    StudySessionCreate,
    StudySessionResponse,
    StudySessionUpdate,
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


def require_group_creator(
    group: StudyGroup,
    current_user: User,
):
    if group.creator_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Only the group creator can manage "
                "study sessions."
            ),
        )


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
                "Only group members can view "
                "study sessions."
            ),
        )


def validate_session_data(
    title: str,
    scheduled_at: datetime,
    duration_minutes: int,
):
    if not title.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session title is required.",
        )

    if duration_minutes <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duration must be greater than zero.",
        )

    current_time = (
        datetime.now(scheduled_at.tzinfo)
        if scheduled_at.tzinfo
        else datetime.now()
    )

    if scheduled_at <= current_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Study sessions must be scheduled in the future.",
        )


@router.post(
    "/study-groups/{group_id}/sessions",
    response_model=StudySessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_study_session(
    group_id: int,
    session_data: StudySessionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    group = get_group_or_404(group_id, db)

    require_group_creator(group, current_user)

    validate_session_data(
        session_data.title,
        session_data.scheduled_at,
        session_data.duration_minutes,
    )

    new_session = StudySession(
        group_id=group_id,
        title=session_data.title.strip(),
        location=(
            session_data.location.strip()
            if session_data.location
            else None
        ),
        meeting_link=(
            session_data.meeting_link.strip()
            if session_data.meeting_link
            else None
        ),
        scheduled_at=session_data.scheduled_at,
        duration_minutes=session_data.duration_minutes,
    )

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return new_session


@router.get(
    "/study-groups/{group_id}/sessions",
    response_model=list[StudySessionResponse],
)
def get_group_sessions(
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

    return (
        db.query(StudySession)
        .filter(
            StudySession.group_id == group_id
        )
        .order_by(
            StudySession.scheduled_at
        )
        .all()
    )


@router.get(
    "/sessions/{session_id}",
    response_model=StudySessionResponse,
)
def get_study_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    study_session = (
        db.query(StudySession)
        .filter(
            StudySession.id == session_id
        )
        .first()
    )

    if not study_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study session not found.",
        )

    group = get_group_or_404(
        study_session.group_id,
        db,
    )

    require_group_member(
        group,
        current_user,
        db,
    )

    return study_session


@router.put(
    "/sessions/{session_id}",
    response_model=StudySessionResponse,
)
def update_study_session(
    session_id: int,
    session_data: StudySessionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    study_session = (
        db.query(StudySession)
        .filter(
            StudySession.id == session_id
        )
        .first()
    )

    if not study_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study session not found.",
        )

    group = get_group_or_404(
        study_session.group_id,
        db,
    )

    require_group_creator(
        group,
        current_user,
    )

    validate_session_data(
        session_data.title,
        session_data.scheduled_at,
        session_data.duration_minutes,
    )

    study_session.title = (
        session_data.title.strip()
    )

    study_session.location = (
        session_data.location.strip()
        if session_data.location
        else None
    )

    study_session.meeting_link = (
        session_data.meeting_link.strip()
        if session_data.meeting_link
        else None
    )

    study_session.scheduled_at = (
        session_data.scheduled_at
    )

    study_session.duration_minutes = (
        session_data.duration_minutes
    )

    db.commit()
    db.refresh(study_session)

    return study_session


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_study_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    study_session = (
        db.query(StudySession)
        .filter(
            StudySession.id == session_id
        )
        .first()
    )

    if not study_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study session not found.",
        )

    group = get_group_or_404(
        study_session.group_id,
        db,
    )

    require_group_creator(
        group,
        current_user,
    )

    db.delete(study_session)
    db.commit()

    return None