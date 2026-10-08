from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.restaurant import Restaurant
from src.schemas.restaurant import RestaurantCreate, RestaurantUpdate


def create_restaurant(
    db: Session,
    restaurant_data: RestaurantCreate,
    manager_id: str | None = None,
) -> Restaurant:
    """
    Crée un restaurant.

    Si manager_id est fourni, le restaurant est automatiquement
    attribué à ce manager.
    """
    restaurant = Restaurant(
        name=restaurant_data.name,
        description=restaurant_data.description,
        address=restaurant_data.address,
        phone=restaurant_data.phone,
        manager_id=manager_id,
    )

    db.add(restaurant)
    db.commit()
    db.refresh(restaurant)

    return restaurant


def get_restaurants(db: Session) -> list[Restaurant]:
    """
    Retourne tous les restaurants.
    """
    result = db.execute(
        select(Restaurant)
    )

    return result.scalars().all()


def get_manager_restaurants(
    db: Session,
    manager_id: str,
) -> list[Restaurant]:
    """
    Retourne uniquement les restaurants attribués à un manager.
    """
    result = db.execute(
        select(Restaurant).where(
            Restaurant.manager_id == manager_id
        )
    )

    return result.scalars().all()


def get_restaurant(
    db: Session,
    restaurant_id: str,
) -> Restaurant:
    """
    Retourne un restaurant à partir de son identifiant.
    """
    restaurant = db.execute(
        select(Restaurant).where(
            Restaurant.id == restaurant_id
        )
    ).scalar_one_or_none()

    if restaurant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant introuvable.",
        )

    return restaurant


def get_manager_restaurant(
    db: Session,
    restaurant_id: str,
    manager_id: str,
) -> Restaurant:
    """
    Retourne un restaurant uniquement s'il appartient au manager.
    """
    restaurant = db.execute(
        select(Restaurant).where(
            Restaurant.id == restaurant_id,
            Restaurant.manager_id == manager_id,
        )
    ).scalar_one_or_none()

    if restaurant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant introuvable ou non attribué à ce manager.",
        )

    return restaurant


def update_restaurant(
    db: Session,
    restaurant_id: str,
    restaurant_data: RestaurantUpdate,
    manager_id: str | None = None,
) -> Restaurant:
    """
    Modifie un restaurant.

    Si manager_id est fourni, le restaurant doit appartenir
    à ce manager.
    """
    if manager_id is not None:
        restaurant = get_manager_restaurant(
            db,
            restaurant_id,
            manager_id,
        )
    else:
        restaurant = get_restaurant(
            db,
            restaurant_id,
        )

    if restaurant_data.name is not None:
        restaurant.name = restaurant_data.name

    if restaurant_data.description is not None:
        restaurant.description = restaurant_data.description

    if restaurant_data.address is not None:
        restaurant.address = restaurant_data.address

    if restaurant_data.phone is not None:
        restaurant.phone = restaurant_data.phone

    db.commit()
    db.refresh(restaurant)

    return restaurant


def delete_restaurant(
    db: Session,
    restaurant_id: str,
    manager_id: str | None = None,
) -> None:
    """
    Supprime un restaurant.

    Si manager_id est fourni, le restaurant doit appartenir
    à ce manager.
    """
    if manager_id is not None:
        restaurant = get_manager_restaurant(
            db,
            restaurant_id,
            manager_id,
        )
    else:
        restaurant = get_restaurant(
            db,
            restaurant_id,
        )

    db.delete(restaurant)
    db.commit()