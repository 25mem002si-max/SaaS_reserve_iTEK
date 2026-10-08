from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.restaurant import Restaurant
from src.models.restaurant_table import RestaurantTable
from src.schemas.restaurant_table import (
    RestaurantTableCreate,
    RestaurantTableUpdate,
)


def get_restaurant_for_manager(
    db: Session,
    restaurant_id: str,
    manager_id: str,
) -> Restaurant:
    """
    Vérifie qu'un restaurant existe et qu'il appartient au manager.
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


def create_restaurant_table(
    db: Session,
    restaurant_id: str,
    table_data: RestaurantTableCreate,
    manager_id: str | None = None,
) -> RestaurantTable:
    """
    Crée une table dans un restaurant.

    Si manager_id est fourni, le restaurant doit appartenir
    à ce manager.
    """
    if manager_id is not None:
        get_restaurant_for_manager(
            db,
            restaurant_id,
            manager_id,
        )
    else:
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

    table = RestaurantTable(
        restaurant_id=restaurant_id,
        table_number=table_data.table_number,
        capacity=table_data.capacity,
        status=table_data.status,
    )

    db.add(table)
    db.commit()
    db.refresh(table)

    return table


def get_restaurant_tables(
    db: Session,
    restaurant_id: str,
    manager_id: str | None = None,
) -> list[RestaurantTable]:
    """
    Retourne les tables d'un restaurant.

    Si manager_id est fourni, le restaurant doit appartenir
    à ce manager.
    """
    if manager_id is not None:
        get_restaurant_for_manager(
            db,
            restaurant_id,
            manager_id,
        )
    else:
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

    result = db.execute(
        select(RestaurantTable).where(
            RestaurantTable.restaurant_id == restaurant_id
        )
    )

    return result.scalars().all()


def get_restaurant_table(
    db: Session,
    table_id: str,
    manager_id: str | None = None,
) -> RestaurantTable:
    """
    Retourne une table précise.

    Si manager_id est fourni, vérifie que la table appartient
    à un restaurant géré par ce manager.
    """
    table = db.execute(
        select(RestaurantTable).where(
            RestaurantTable.id == table_id
        )
    ).scalar_one_or_none()

    if table is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table introuvable.",
        )

    if manager_id is not None:
        get_restaurant_for_manager(
            db,
            table.restaurant_id,
            manager_id,
        )

    return table


def update_restaurant_table(
    db: Session,
    table_id: str,
    table_data: RestaurantTableUpdate,
    manager_id: str | None = None,
) -> RestaurantTable:
    """
    Modifie une table.

    Le contrôle du manager est effectué avant toute modification.
    """
    table = get_restaurant_table(
        db,
        table_id,
        manager_id,
    )

    if table_data.table_number is not None:
        table.table_number = table_data.table_number

    if table_data.capacity is not None:
        table.capacity = table_data.capacity

    if table_data.status is not None:
        table.status = table_data.status

    db.commit()
    db.refresh(table)

    return table


def delete_restaurant_table(
    db: Session,
    table_id: str,
    manager_id: str | None = None,
) -> None:
    """
    Supprime une table.

    Le contrôle du manager est effectué avant la suppression.
    """
    table = get_restaurant_table(
        db,
        table_id,
        manager_id,
    )

    db.delete(table)
    db.commit()