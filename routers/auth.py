from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import AuthResponse, UserLogin, UserRegister
from security import hash_password, verify_password

router = APIRouter()


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED
)
def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    if len(user_data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 6 characters long."
        )

    existing_user = (
        db.query(User)
        .filter(User.email == str(user_data.email))
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists."
        )

    new_user = User(
        display_name=user_data.display_name,
        email=str(user_data.email),
        password_hash=hash_password(user_data.password),
        major=user_data.major,
        school_year=user_data.school_year
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully.",
        "user": new_user
    }


@router.post(
    "/login",
    response_model=AuthResponse
)
def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.email == str(login_data.email))
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    password_is_valid = verify_password(
        login_data.password,
        user.password_hash
    )

    if not password_is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    return {
        "message": "Login successful.",
        "user": user
    }