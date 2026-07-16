from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from routers import auth
from routers import dashboard
from routers import discussion_posts
from routers import group_members
from routers import study_groups
from routers import study_sessions
from routers import users


app = FastAPI(title="StudyFinder API")


app.include_router(
    users.router,
    prefix="/users",
    tags=["Users"]
)

app.include_router(
    study_groups.router,
    prefix="/study-groups",
    tags=["Study Groups"]
)

app.include_router(
    group_members.router,
    prefix="/study-groups",
    tags=["Group Members"]
)

app.include_router(
    study_sessions.router,
    tags=["Study Sessions"]
)

app.include_router(
    discussion_posts.router,
    tags=["Discussion Posts"]
)

app.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["Dashboard"]
)

app.include_router(
    auth.router,
    prefix="/auth",
    tags=["Auth"]
)


# This must remain after all API routers.
frontend_directory = Path(__file__).resolve().parent / "frontend"

app.mount(
    "/",
    StaticFiles(
        directory=frontend_directory,
        html=True
    ),
    name="frontend"
)