from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from auth_dependencies import get_current_user
from database import get_db
from models import (
    Invitation,
    StudyGroup,
    StudyGroupMember,
    StudySession,
    User
)
from schemas import InvitationCreate, InvitationResponse


router = APIRouter(
    prefix="/invitations",
    tags=["Invitations"]
)



@router.post(
    "/groups/{group_id}",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED
)
def send_group_invitation(
    group_id: int,
    invitation_data: InvitationCreate,
    current_user: User = Depends(get_current_user),
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

    if group.creator_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the group creator can send invitations."
        )

    invitee = (
        db.query(User)
        .filter(
            User.email.ilike(str(invitation_data.invitee_email))
        )
        .first()
    )

    if not invitee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No registered user has this email."
        )

    if invitee.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot invite yourself."
        )

    existing_member = (
        db.query(StudyGroupMember)
        .filter(
            StudyGroupMember.group_id == group_id,
            StudyGroupMember.user_id == invitee.id
        )
        .first()
    )

    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This user is already a group member."
        )

    existing_invitation = (
        db.query(Invitation)
        .filter(
            Invitation.invitee_user_id == invitee.id,
            Invitation.group_id == group_id,
            Invitation.invitation_type == "group",
            Invitation.status == "pending"
        )
        .first()
    )

    if existing_invitation:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This user already has a pending invitation."
        )

    new_invitation = Invitation(
        inviter_user_id=current_user.id,
        invitee_user_id=invitee.id,
        invitation_type="group",
        group_id=group_id,
        session_id=None,
        status="pending"
    )

    db.add(new_invitation)
    db.commit()
    db.refresh(new_invitation)

    return new_invitation





@router.post(
    "/sessions/{session_id}",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED
)
def send_session_invitation(
    session_id: int,
    invitation_data: InvitationCreate,
    current_user: User = Depends(get_current_user),
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

    group = (
        db.query(StudyGroup)
        .filter(StudyGroup.id == study_session.group_id)
        .first()
    )

    if group.creator_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the group creator can send session invitations."
        )

    invitee = (
        db.query(User)
        .filter(
            User.email.ilike(str(invitation_data.invitee_email))
        )
        .first()
    )

    if not invitee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No registered user has this email."
        )

    if invitee.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot invite yourself."
        )

    group_member = (
        db.query(StudyGroupMember)
        .filter(
            StudyGroupMember.group_id == group.id,
            StudyGroupMember.user_id == invitee.id
        )
        .first()
    )

    if not group_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The invited user must be a member of the group."
        )

    existing_invitation = (
        db.query(Invitation)
        .filter(
            Invitation.invitee_user_id == invitee.id,
            Invitation.session_id == session_id,
            Invitation.invitation_type == "session",
            Invitation.status == "pending"
        )
        .first()
    )

    if existing_invitation:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This user already has a pending session invitation."
        )

    new_invitation = Invitation(
        inviter_user_id=current_user.id,
        invitee_user_id=invitee.id,
        invitation_type="session",
        group_id=group.id,
        session_id=session_id,
        status="pending"
    )

    db.add(new_invitation)
    db.commit()
    db.refresh(new_invitation)

    return new_invitation



@router.get(
    "/mine",
    response_model=list[InvitationResponse]
)
def get_my_invitations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    invitations = (
        db.query(Invitation)
        .filter(
            Invitation.invitee_user_id == current_user.id
        )
        .order_by(Invitation.created_at.desc())
        .all()
    )

    results = []

    for invitation in invitations:
        inviter = (
            db.query(User)
            .filter(User.id == invitation.inviter_user_id)
            .first()
        )

        group = None
        study_session = None

        if invitation.group_id:
            group = (
                db.query(StudyGroup)
                .filter(StudyGroup.id == invitation.group_id)
                .first()
            )

        if invitation.session_id:
            study_session = (
                db.query(StudySession)
                .filter(StudySession.id == invitation.session_id)
                .first()
            )

        results.append({
            "id": invitation.id,
            "inviter_user_id": invitation.inviter_user_id,
            "invitee_user_id": invitation.invitee_user_id,
            "invitation_type": invitation.invitation_type,
            "group_id": invitation.group_id,
            "session_id": invitation.session_id,
            "status": invitation.status,
            "created_at": invitation.created_at,
            "responded_at": invitation.responded_at,
            "inviter_name": (
                inviter.display_name if inviter else None
            ),
            "group_name": (
                group.group_name if group else None
            ),
            "session_title": (
                study_session.title if study_session else None
            )
        })

    return results





@router.put(
    "/{invitation_id}/accept",
    response_model=InvitationResponse
)
def accept_invitation(
    invitation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    invitation = (
        db.query(Invitation)
        .filter(Invitation.id == invitation_id)
        .first()
    )

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found."
        )

    if invitation.invitee_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invitation does not belong to you."
        )

    if invitation.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This invitation has already been answered."
        )

    if invitation.invitation_type == "group":
        group = (
            db.query(StudyGroup)
            .filter(StudyGroup.id == invitation.group_id)
            .first()
        )

        if not group:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Study group not found."
            )

        member_count = (
            db.query(StudyGroupMember)
            .filter(
                StudyGroupMember.group_id == group.id
            )
            .count()
        )

        if member_count >= group.max_members:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This study group is full."
            )

        existing_member = (
            db.query(StudyGroupMember)
            .filter(
                StudyGroupMember.group_id == group.id,
                StudyGroupMember.user_id == current_user.id
            )
            .first()
        )

        if existing_member:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You are already a member of this group."
            )

        new_member = StudyGroupMember(
            group_id=group.id,
            user_id=current_user.id
        )

        db.add(new_member)

    elif invitation.invitation_type == "session":
        group_member = (
            db.query(StudyGroupMember)
            .filter(
                StudyGroupMember.group_id == invitation.group_id,
                StudyGroupMember.user_id == current_user.id
            )
            .first()
        )

        if not group_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must belong to the group to accept this session invitation."
            )

    invitation.status = "accepted"
    invitation.responded_at = datetime.now()

    db.commit()
    db.refresh(invitation)

    return invitation



@router.put(
    "/{invitation_id}/decline",
    response_model=InvitationResponse
)
def decline_invitation(
    invitation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    invitation = (
        db.query(Invitation)
        .filter(Invitation.id == invitation_id)
        .first()
    )

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found."
        )

    if invitation.invitee_user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invitation does not belong to you."
        )

    if invitation.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This invitation has already been answered."
        )

    invitation.status = "declined"
    invitation.responded_at = datetime.now()

    db.commit()
    db.refresh(invitation)

    return invitation