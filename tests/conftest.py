"""
Shared pytest fixtures for the StudyFinder test suite.

Tests run against a dedicated SQLite file (test_studyfinder.db) so they never
touch your real studyfinder.db. Each test function gets a freshly wiped
database, so tests don't leak state into one another.
"""

import os
import sys
from pathlib import Path

# Make sure the project root (where main.py lives) is importable.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Point the app at a throwaway test database *before* anything imports it.
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_studyfinder.db")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app

TEST_DATABASE_URL = "sqlite:///./test_studyfinder.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


@pytest.fixture()
def db_session():
    """A clean database for a single test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    """A TestClient wired up to use the clean test database."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------
# Small helpers reused across test files
# ---------------------------------------------------------------------

def register_user(client, display_name="Test User", email="test@uncc.edu",
                   password="password123", major="Computer Science"):
    response = client.post(
        "/auth/register",
        json={
            "display_name": display_name,
            "email": email,
            "password": password,
            "major": major,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()["user"]


def create_group(client, creator_user_id, group_name="Database Systems",
                  course_code="ITIS-3300", max_members=10):
    response = client.post(
        "/study-groups/",
        json={
            "group_name": group_name,
            "course_code": course_code,
            "description": "Weekly study sessions.",
            "creator_user_id": creator_user_id,
            "status": "open",
            "max_members": max_members,
        },
    )
    assert response.status_code == 201, response.text
    return response.json()
