from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.enums.role import UserRole
from src.models.user import User
from src.schemas.restaurant_table import (
    RestaurantTableCreate,
    RestaurantTableResponse,
    RestaurantTableUpdate,
)
from src.security.auth import get_current_user
from src.services.restaurant_table_service import (
    create_restaurant_table,
    delete_restaurant_table,
    get_restaurant_table,
    get_restaurant_tables,
    update_restaurant_table,
)


router = APIRouter(
    prefix="/restaurants",
    tags=["Restaurant Tables"],
)


@router.post(
    "/{restaurant_id}/tables",
    response_model=RestaurantTableResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_table_endpoint(
    restaurant_id: UUID,
    table_data: RestaurantTableCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Crée une table dans un restaurant.

    - ADMIN : peut créer une table dans n'importe quel restaurant.
    - MANAGER : peut créer une table uniquement dans son restaurant.
    - CLIENT : accès interdit.
    """
    if current_user.role == UserRole.ADMIN.value:
        return create_restaurant_table(
            db,
            str(restaurant_id),
            table_data,
        )

    if current_user.role == UserRole.MANAGER.value:
        return create_restaurant_table(
            db,
            str(restaurant_id),
            table_data,
            manager_id=str(current_user.id),
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Seuls les administrateurs et les managers peuvent créer une table.",
    )


@router.get(
    "/{restaurant_id}/tables",
    response_model=list[RestaurantTableResponse],
)
def get_tables_endpoint(
    restaurant_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retourne les tables d'un restaurant.

    - ADMIN : peut consulter les tables de n'importe quel restaurant.
    - MANAGER : peut consulter les tables de son restaurant.
    - CLIENT : peut consulter les tables pour effectuer une réservation.
    """
    if current_user.role == UserRole.ADMIN.value:
        return get_restaurant_tables(
            db,
            str(restaurant_id),
        )

    if current_user.role == UserRole.MANAGER.value:
        return get_restaurant_tables(
            db,
            str(restaurant_id),
            manager_id=str(current_user.id),
        )

    if current_user.role == UserRole.CLIENT.value:
        return get_restaurant_tables(
            db,
            str(restaurant_id),
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Accès refusé.",
    )


@router.get(
    "/tables/{table_id}",
    response_model=RestaurantTableResponse,
)
def get_table_endpoint(
    table_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retourne une table précise.

    - ADMIN : peut consulter n'importe quelle table.
    - MANAGER : peut consulter uniquement une table de son restaurant.
    - CLIENT : peut consulter une table.
    """
    if current_user.role == UserRole.ADMIN.value:
        return get_restaurant_table(
            db,
            str(table_id),
        )

    if current_user.role == UserRole.MANAGER.value:
        return get_restaurant_table(
            db,
            str(table_id),
            manager_id=str(current_user.id),
        )

    if current_user.role == UserRole.CLIENT.value:
        return get_restaurant_table(
            db,
            str(table_id),
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Accès refusé.",
    )


@router.put(
    "/tables/{table_id}",
    response_model=RestaurantTableResponse,
)
def update_table_endpoint(
    table_id: UUID,
    table_data: RestaurantTableUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Modifie une table.

    - ADMIN : peut modifier n'importe quelle table.
    - MANAGER : peut modifier uniquement une table de son restaurant.
    - CLIENT : accès interdit.
    """
    if current_user.role == UserRole.ADMIN.value:
        return update_restaurant_table(
            db,
            str(table_id),
            table_data,
        )

    if current_user.role == UserRole.MANAGER.value:
        return update_restaurant_table(
            db,
            str(table_id),
            table_data,
            manager_id=str(current_user.id),
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Seuls les administrateurs et les managers peuvent modifier une table.",
    )


@router.delete(
    "/tables/{table_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_table_endpoint(
    table_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Supprime une table.

    - ADMIN : peut supprimer n'importe quelle table.
    - MANAGER : peut supprimer uniquement une table de son restaurant.
    - CLIENT : accès interdit.
    """
    if current_user.role == UserRole.ADMIN.value:
        delete_restaurant_table(
            db,
            str(table_id),
        )
        return None

    if current_user.role == UserRole.MANAGER.value:
        delete_restaurant_table(
            db,
            str(table_id),
            manager_id=str(current_user.id),
        )
        return None

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Seuls les administrateurs et les managers peuvent supprimer une table.",
    )