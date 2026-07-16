from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    major: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    school_year: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )


class StudyGroup(Base):
    __tablename__ = "study_groups"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    group_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    course_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    creator_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="open"
    )

    max_members: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )


class StudyGroupMember(Base):
    __tablename__ = "study_group_members"

    group_id: Mapped[int] = mapped_column(
        ForeignKey("study_groups.id", ondelete="CASCADE"),
        primary_key=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )


class StudySession(Base):
    __tablename__ = "study_sessions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    group_id: Mapped[int] = mapped_column(
        ForeignKey("study_groups.id", ondelete="CASCADE"),
        nullable=False
    )

    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    location: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True
    )

    meeting_link: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False
    )

    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=60
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    message: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )


class DiscussionPost(Base):
    __tablename__ = "discussion_posts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    group_id: Mapped[int] = mapped_column(
        ForeignKey("study_groups.id", ondelete="CASCADE"),
        nullable=False
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    title: Mapped[str] = mapped_column(
        String(150),
        nullable=False
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now()
    )