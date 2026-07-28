from pathlib import Path
from fastapi import Depends, FastAPI
from auth_dependencies import get_current_user
from fastapi.staticfiles import StaticFiles
import models
from database import Base, engine
from routers import auth
from routers import dashboard
from routers import discussion_posts
from routers import group_members
from routers import study_groups
from routers import study_sessions
from routers import users
from routers import invitations



Base.metadata.create_all(bind=engine)
app = FastAPI(title="StudyFinder API")

app.include_router(
    auth.router,
    prefix="/auth",
    tags=["Auth"]
)

app.include_router(
    users.router,
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    study_groups.router,
    prefix="/study-groups",
    tags=["Study Groups"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    group_members.router,
    prefix="/study-groups",
    tags=["Group Members"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    study_sessions.router,
    tags=["Study Sessions"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    discussion_posts.router,
    tags=["Discussion Posts"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(get_current_user)]
)

app.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(get_current_user)]
)


app.include_router(invitations.router)


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