from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import User
from schemas import AuthResponse, UserLogin, UserRegister
from security import (
    create_access_token,
    hash_password,
    verify_password,
)

router = APIRouter()


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db),
):
    # 1. Check whether the email is already registered.
    existing_user = (
        db.query(User)
        .filter(User.email == user_data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    # 2. Hash the password before saving it.
    password_hash = hash_password(user_data.password)

    # 3. Create the user record.
    new_user = User(
        display_name=user_data.display_name,
        email=user_data.email,
        password_hash=password_hash,
        major=user_data.major,
        school_year=user_data.school_year,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 4. Create a JWT containing the new user's ID.
    access_token = create_access_token(new_user.id)

    # 5. Return the token and safe user information.
    return {
        "message": "Account created successfully.",
        "access_token": access_token,
        "token_type": "bearer",
        "user": new_user,
    }


@router.post(
    "/login",
    response_model=AuthResponse,
)
def login_user(
    login_data: UserLogin,
    db: Session = Depends(get_db),
):
    # 1. Find the account using the submitted email.
    user = (
        db.query(User)
        .filter(User.email == login_data.email)
        .first()
    )

    # 2. Stop if the email does not exist.
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # 3. Compare the submitted password with the saved hash.
    password_is_valid = verify_password(
        login_data.password,
        user.password_hash,
    )

    if not password_is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # 4. Create a signed JWT containing this user's ID.
    access_token = create_access_token(user.id)

    # 5. Return the token and safe user information.
    return {
        "message": "Login successful.",
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
    }