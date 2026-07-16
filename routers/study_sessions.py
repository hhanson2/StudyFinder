from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import StudyGroup, StudySession
from schemas import StudySessionCreate, StudySessionResponse, StudySessionUpdate

router = APIRouter()


@router.post(
    "/study-groups/{group_id}/sessions",
    response_model=StudySessionResponse,
    status_code=status.HTTP_201_CREATED
)
def create_study_session(
    group_id: int,
    session_data: StudySessionCreate,
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

    if session_data.duration_minutes <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duration must be greater than zero."
        )

    new_session = StudySession(
        group_id=group_id,
        title=session_data.title,
        location=session_data.location,
        meeting_link=session_data.meeting_link,
        scheduled_at=session_data.scheduled_at,
        duration_minutes=session_data.duration_minutes
    )

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    return new_session


@router.get(
    "/study-groups/{group_id}/sessions",
    response_model=list[StudySessionResponse]
)
def get_group_sessions(
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

    return (
        db.query(StudySession)
        .filter(StudySession.group_id == group_id)
        .order_by(StudySession.scheduled_at)
        .all()
    )


@router.get(
    "/sessions/{session_id}",
    response_model=StudySessionResponse
)
def get_study_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    study_session = (
        db.query(StudySession)
        .filter(StudySession.id == session_id)
        .first()
    )

    if not study_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study session not found."
        )

    return study_session


@router.put(
    "/sessions/{session_id}",
    response_model=StudySessionResponse
)
def update_study_session(
    session_id: int,
    session_data: StudySessionUpdate,
    db: Session = Depends(get_db)
):
    study_session = (
        db.query(StudySession)
        .filter(StudySession.id == session_id)
        .first()
    )

    if not study_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study session not found."
        )

    if session_data.duration_minutes <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Duration must be greater than zero."
        )

    study_session.title = session_data.title
    study_session.location = session_data.location
    study_session.meeting_link = session_data.meeting_link
    study_session.scheduled_at = session_data.scheduled_at
    study_session.duration_minutes = session_data.duration_minutes

    db.commit()
    db.refresh(study_session)

    return study_session


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def delete_study_session(
    session_id: int,
    db: Session = Depends(get_db)
):
    study_session = (
        db.query(StudySession)
        .filter(StudySession.id == session_id)
        .first()
    )

    if not study_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study session not found."
        )

    db.delete(study_session)
    db.commit()

    return None