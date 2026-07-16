from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_database
from models import SessionModel, SessionParticipant, User
from schemas import ParticipantCreate, ParticipantResponse


router = APIRouter(
    prefix="/sessions",
    tags=["Participants"]
)


@router.post(
    "/{session_id}/participants",
    response_model=ParticipantResponse,
    status_code=status.HTTP_201_CREATED
)
def join_session(
    session_id: int,
    participant_data: ParticipantCreate,
    database: Session = Depends(get_database)
) -> SessionParticipant:

    session_record = database.get(SessionModel, session_id)

    if session_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found."
        )

    user = database.get(User, participant_data.user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found."
        )

    existing_participant = database.get(
        SessionParticipant,
        (session_id, participant_data.user_id)
    )

    if existing_participant is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User has already joined this session."
        )

    participant_count = database.scalar(
        select(func.count())
        .select_from(SessionParticipant)
        .where(SessionParticipant.session_id == session_id)
    )

    if participant_count >= session_record.max_participants:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The session has reached its participant limit."
        )

    new_participant = SessionParticipant(
        session_id=session_id,
        user_id=participant_data.user_id
    )

    database.add(new_participant)

    try:
        database.commit()
        database.refresh(new_participant)
        return new_participant

    except IntegrityError:
        database.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The user could not join the session."
        )


@router.get(
    "/{session_id}/participants",
    response_model=list[ParticipantResponse],
)
def get_session_participants(
    session_id: int,
    database: Session = Depends(get_database),
):
    session_record = database.get(SessionModel, session_id)

    if session_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )

    statement = (
        select(SessionParticipant)
        .where(SessionParticipant.session_id == session_id)
        .order_by(SessionParticipant.joined_at)
    )

    participants = database.scalars(statement).all()

    return participants


@router.delete(
    "/{session_id}/participants/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def leave_session(
    session_id: int,
    user_id: int,
    database: Session = Depends(get_database),
) -> Response:
    participant = database.get(
        SessionParticipant,
        (session_id, user_id),
    )

    if participant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The user is not a participant in this session.",
        )

    database.delete(participant)
    database.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)