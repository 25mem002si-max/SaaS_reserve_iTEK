from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.enums.role import UserRole
from src.models.user import User
from src.schemas.user import UserCreate, UserResponse, UserUpdate
from src.security.auth import get_current_admin, get_current_user
from src.services.user_service import create_user, get_users


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user_endpoint(
    user_data: UserCreate,
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Crée un nouvel utilisateur.

    Toute inscription publique crée un utilisateur avec le rôle CLIENT.
    Le rôle envoyé par le client est volontairement ignoré.
    """

    user_data.role = UserRole.CLIENT

    try:
        return create_user(db, user_data)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Le nom d'utilisateur ou l'adresse e-mail existe déjà.",
        )


@router.get(
    "",
    response_model=list[UserResponse],
)
def get_users_endpoint(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> list[User]:
    """
    Retourne la liste de tous les utilisateurs.

    Accès réservé aux administrateurs.
    """

    return get_users(db)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user_endpoint(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Retourne le profil d'un utilisateur.

    Un utilisateur peut consulter son propre profil.
    Un administrateur peut consulter n'importe quel utilisateur.
    """

    user = db.execute(
        select(User).where(User.id == str(user_id))
    ).scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable.",
        )

    is_admin = current_user.role == UserRole.ADMIN.value
    is_own_profile = str(current_user.id) == str(user_id)

    if not is_admin and not is_own_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à consulter cet utilisateur.",
        )

    return user


@router.put(
    "/{user_id}",
    response_model=UserResponse,
)
def update_user_endpoint(
    user_id: UUID,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Modifie le profil d'un utilisateur.

    Un utilisateur peut modifier son propre profil.
    Seul un administrateur peut modifier le rôle.
    """

    user = db.execute(
        select(User).where(User.id == str(user_id))
    ).scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable.",
        )

    is_admin = current_user.role == UserRole.ADMIN.value
    is_own_profile = str(current_user.id) == str(user_id)

    # Protection contre la modification du profil d'un autre utilisateur.
    if not is_admin and not is_own_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à modifier cet utilisateur.",
        )

    # Seul un administrateur peut modifier le rôle.
    if user_data.role is not None and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seul un administrateur peut modifier un rôle.",
        )

    if user_data.username is not None:
        user.username = user_data.username

    if user_data.email is not None:
        user.email = user_data.email

    if user_data.role is not None:
        user.role = user_data.role.value

    try:
        db.commit()
        db.refresh(user)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Le nom d'utilisateur ou l'adresse e-mail existe déjà.",
        )

    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_user_endpoint(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
) -> None:
    """
    Supprime un utilisateur.

    Accès réservé aux administrateurs.
    """

    user = db.execute(
        select(User).where(User.id == str(user_id))
    ).scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable.",
        )

    # Évite qu'un administrateur supprime accidentellement son propre compte.
    if str(user.id) == str(current_admin.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un administrateur ne peut pas supprimer son propre compte.",
        )

    db.delete(user)
    db.commit()

    return None