from datetime import date, time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.enums.role import UserRole
from src.models.user import User
from src.schemas.availability import AvailabilityResponse
from src.schemas.restaurant import (
    RestaurantCreate,
    RestaurantResponse,
    RestaurantUpdate,
)
from src.security.auth import get_current_user
from src.services.availability_service import get_available_tables
from src.services.restaurant_service import (
    create_restaurant,
    delete_restaurant,
    get_manager_restaurant,
    get_manager_restaurants,
    get_restaurant,
    get_restaurants,
    update_restaurant,
)


router = APIRouter(
    prefix="/restaurants",
    tags=["Restaurants"],
)


@router.post(
    "",
    response_model=RestaurantResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_restaurant_endpoint(
    restaurant_data: RestaurantCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Crée un restaurant.

    ADMIN :
        Peut créer un restaurant sans manager obligatoire.

    MANAGER :
        Le restaurant créé lui est automatiquement attribué.

    CLIENT :
        Accès interdit.
    """
    if current_user.role == UserRole.ADMIN.value:
        return create_restaurant(
            db,
            restaurant_data,
        )

    if current_user.role == UserRole.MANAGER.value:
        return create_restaurant(
            db,
            restaurant_data,
            manager_id=str(current_user.id),
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "Seuls les administrateurs et les managers "
            "peuvent créer un restaurant."
        ),
    )


@router.get(
    "",
    response_model=list[RestaurantResponse],
)
def get_restaurants_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retourne les restaurants accessibles à l'utilisateur.

    ADMIN :
        Tous les restaurants.

    MANAGER :
        Uniquement ses restaurants.

    CLIENT :
        Les restaurants disponibles.
    """
    if current_user.role == UserRole.ADMIN.value:
        return get_restaurants(db)

    if current_user.role == UserRole.MANAGER.value:
        return get_manager_restaurants(
            db,
            str(current_user.id),
        )

    return get_restaurants(db)


@router.get(
    "/{restaurant_id}/availability",
    response_model=AvailabilityResponse,
)
def get_restaurant_availability_endpoint(
    restaurant_id: UUID,
    reservation_date: date = Query(
        ...,
        description="Date souhaitée de la réservation.",
    ),
    reservation_time: time = Query(
        ...,
        description="Heure souhaitée de la réservation.",
    ),
    number_of_people: int = Query(
        ...,
        gt=0,
        description="Nombre de personnes.",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retourne les tables disponibles d'un restaurant
    pour une date, une heure et un nombre de personnes donnés.

    CLIENT :
        Peut rechercher la disponibilité.

    MANAGER :
        Peut rechercher la disponibilité de ses restaurants.

    ADMIN :
        Peut rechercher la disponibilité de tous les restaurants.
    """
    restaurant_id_str = str(restaurant_id)

    if current_user.role == UserRole.ADMIN.value:
        return get_available_tables(
            db=db,
            restaurant_id=restaurant_id_str,
            reservation_date=reservation_date,
            reservation_time=reservation_time,
            number_of_people=number_of_people,
        )

    if current_user.role == UserRole.MANAGER.value:
        # Vérifie que le restaurant appartient bien au manager.
        get_manager_restaurant(
            db,
            restaurant_id_str,
            str(current_user.id),
        )

        return get_available_tables(
            db=db,
            restaurant_id=restaurant_id_str,
            reservation_date=reservation_date,
            reservation_time=reservation_time,
            number_of_people=number_of_people,
        )

    if current_user.role == UserRole.CLIENT.value:
        return get_available_tables(
            db=db,
            restaurant_id=restaurant_id_str,
            reservation_date=reservation_date,
            reservation_time=reservation_time,
            number_of_people=number_of_people,
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Accès interdit.",
    )


@router.get(
    "/{restaurant_id}",
    response_model=RestaurantResponse,
)
def get_restaurant_endpoint(
    restaurant_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retourne un restaurant.

    ADMIN :
        Peut consulter n'importe quel restaurant.

    MANAGER :
        Peut consulter uniquement son restaurant.

    CLIENT :
        Peut consulter les restaurants.
    """
    restaurant_id_str = str(restaurant_id)

    if current_user.role == UserRole.ADMIN.value:
        return get_restaurant(
            db,
            restaurant_id_str,
        )

    if current_user.role == UserRole.MANAGER.value:
        return get_manager_restaurant(
            db,
            restaurant_id_str,
            str(current_user.id),
        )

    return get_restaurant(
        db,
        restaurant_id_str,
    )


@router.put(
    "/{restaurant_id}",
    response_model=RestaurantResponse,
)
def update_restaurant_endpoint(
    restaurant_id: UUID,
    restaurant_data: RestaurantUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Modifie un restaurant.

    ADMIN :
        Peut modifier n'importe quel restaurant.

    MANAGER :
        Peut modifier uniquement son restaurant.

    CLIENT :
        Accès interdit.
    """
    restaurant_id_str = str(restaurant_id)

    if current_user.role == UserRole.ADMIN.value:
        return update_restaurant(
            db,
            restaurant_id_str,
            restaurant_data,
        )

    if current_user.role == UserRole.MANAGER.value:
        return update_restaurant(
            db,
            restaurant_id_str,
            restaurant_data,
            manager_id=str(current_user.id),
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "Seuls les administrateurs et les managers "
            "peuvent modifier un restaurant."
        ),
    )


@router.delete(
    "/{restaurant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_restaurant_endpoint(
    restaurant_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Supprime un restaurant.

    ADMIN :
        Peut supprimer n'importe quel restaurant.

    MANAGER :
        Peut supprimer uniquement son restaurant.

    CLIENT :
        Accès interdit.
    """
    restaurant_id_str = str(restaurant_id)

    if current_user.role == UserRole.ADMIN.value:
        delete_restaurant(
            db,
            restaurant_id_str,
        )
        return None

    if current_user.role == UserRole.MANAGER.value:
        delete_restaurant(
            db,
            restaurant_id_str,
            manager_id=str(current_user.id),
        )
        return None

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "Seuls les administrateurs et les managers "
            "peuvent supprimer un restaurant."
        ),
    )