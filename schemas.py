from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict


class UserCreate(BaseModel):
    display_name: str
    email: EmailStr
    major: str | None = None
    school_year: str | None = None

class UserRegister(BaseModel):
    display_name: str
    email: EmailStr
    password: str
    major: str | None = None
    school_year: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class AuthUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    display_name: str
    email: EmailStr
    major: str | None = None
    school_year: str | None = None


class AuthResponse(BaseModel):
    message: str
    access_token: str
    token_type: str
    user: AuthUserResponse

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    display_name: str
    email: EmailStr
    major: str | None = None
    school_year: str | None = None
    created_at: datetime

class UserUpdate(BaseModel):
    display_name: str
    major: str | None = None
    school_year: str | None = None

class StudyGroupCreate(BaseModel):
    group_name: str
    course_code: str
    description: str | None = None
    status: str = "open"
    max_members: int = 10


class StudyGroupUpdate(BaseModel):
    group_name: str
    course_code: str
    description: str | None = None
    status: str = "open"
    max_members: int = 10


class StudyGroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    group_name: str
    course_code: str
    description: str | None = None
    creator_user_id: int
    status: str
    max_members: int
    created_at: datetime


class StudySessionCreate(BaseModel):
    title: str
    location: str | None = None
    meeting_link: str | None = None
    scheduled_at: datetime
    duration_minutes: int = 60


class StudySessionUpdate(BaseModel):
    title: str
    location: str | None = None
    meeting_link: str | None = None
    scheduled_at: datetime
    duration_minutes: int = 60


class StudySessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    group_id: int
    title: str
    location: str | None = None
    meeting_link: str | None = None
    scheduled_at: datetime
    duration_minutes: int
    created_at: datetime


class StudyGroupMemberResponse(BaseModel):
    user_id: int
    display_name: str
    email: EmailStr
    joined_at: datetime


class DiscussionPostCreate(BaseModel):
    title: str
    content: str


class DiscussionPostUpdate(BaseModel):
    title: str
    content: str


class DiscussionPostResponse(BaseModel):
    id: int
    group_id: int
    user_id: int
    display_name: str
    title: str
    content: str
    created_at: datetime


class DiscussionReplyCreate(BaseModel):
    content: str


class DiscussionReplyUpdate(BaseModel):
    content: str


class DiscussionReplyResponse(BaseModel):
    id: int
    post_id: int
    user_id: int
    display_name: str
    content: str
    created_at: datetime


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    message: str
    is_read: bool
    created_at: datetime

class InvitationCreate(BaseModel):
    invitee_email: EmailStr

class InvitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    inviter_user_id: int
    invitee_user_id: int
    invitation_type: str
    group_id: int | None = None
    session_id: int | None = None
    status: str
    created_at: datetime
    responded_at: datetime | None = None


    inviter_name: str | None = None
    group_name: str | None = None
    session_title: str | None = None