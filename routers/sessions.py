from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.orm import Session

from database import get_database
from models import SessionModel, User
from schemas import SessionCreate, SessionResponse


router = APIRouter(
    prefix="/sessions",
    tags=["Sessions"],
)


@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_session(
    session_data: SessionCreate,
    database: Session = Depends(get_database),
) -> SessionModel:
    host = database.get(User, session_data.host_user_id)

    if host is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Host user not found.",
        )

    new_session = SessionModel(
        title=session_data.title,
        description=session_data.description,
        session_type=session_data.session_type,
        category=session_data.category,
        host_user_id=session_data.host_user_id,
        status=session_data.status,
        scheduled_at=session_data.scheduled_at,
        max_participants=session_data.max_participants,
    )

    database.add(new_session)

    try:
        database.commit()
        database.refresh(new_session)
        return new_session

    except (IntegrityError, DataError):
        database.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The session contains invalid data.",
        )


@router.get(
    "",
    response_model=list[SessionResponse],
)
def get_all_sessions(
    database: Session = Depends(get_database),
) -> list[SessionModel]:
    statement = select(SessionModel).order_by(SessionModel.id)
    return list(database.scalars(statement).all())


@router.get(
    "/{session_id}",
    response_model=SessionResponse,
)
def get_session(
    session_id: int,
    database: Session = Depends(get_database),
) -> SessionModel:
    session_record = database.get(SessionModel, session_id)

    if session_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )

    return session_record


@router.put(
    "/{session_id}",
    response_model=SessionResponse,
)
def update_session(
    session_id: int,
    session_data: SessionCreate,
    database: Session = Depends(get_database),
) -> SessionModel:
    session_record = database.get(SessionModel, session_id)

    if session_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )

    host = database.get(User, session_data.host_user_id)

    if host is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Host user not found.",
        )

    session_record.title = session_data.title
    session_record.description = session_data.description
    session_record.session_type = session_data.session_type
    session_record.category = session_data.category
    session_record.host_user_id = session_data.host_user_id
    session_record.status = session_data.status
    session_record.scheduled_at = session_data.scheduled_at
    session_record.max_participants = session_data.max_participants

    try:
        database.commit()
        database.refresh(session_record)
        return session_record

    except (IntegrityError, DataError):
        database.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The session contains invalid data.",
        )


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_session(
    session_id: int,
    database: Session = Depends(get_database),
) -> Response:
    session_record = database.get(SessionModel, session_id)

    if session_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )

    database.delete(session_record)
    database.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)