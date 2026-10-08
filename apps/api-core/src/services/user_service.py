from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.models.user import User
from src.schemas.user import UserCreate
from src.security.security import hash_password


def create_user(
    db: Session,
    user_data: UserCreate,
) -> User:
    existing_username = db.execute(
        select(User).where(
            User.username == user_data.username
        )
    ).scalar_one_or_none()

    if existing_username is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ce nom d'utilisateur est déjà utilisé.",
        )

    existing_email = db.execute(
        select(User).where(
            User.email == user_data.email
        )
    ).scalar_one_or_none()

    if existing_email is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cet email est déjà utilisé.",
        )

    password_hash = hash_password(
        user_data.password
    )

    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=password_hash,
        role=user_data.role.value,
    )

    db.add(user)

    try:
        db.commit()
        db.refresh(user)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Le nom d'utilisateur ou l'email est déjà utilisé.",
        )

    return user


def get_users(
    db: Session,
) -> list[User]:
    result = db.execute(
        select(User)
    )

    return result.scalars().all()