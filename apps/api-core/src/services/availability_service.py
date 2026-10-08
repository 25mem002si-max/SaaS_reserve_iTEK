from datetime import date, time

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.reservation import Reservation
from src.models.restaurant import Restaurant
from src.models.restaurant_table import RestaurantTable
from src.schemas.availability import (
    AvailabilityResponse,
    AvailableTableResponse,
)


ACTIVE_RESERVATION_STATUSES = {
    "pending",
    "confirmed",
}


def get_available_tables(
    db: Session,
    restaurant_id: str,
    reservation_date: date,
    reservation_time: time,
    number_of_people: int,
) -> AvailabilityResponse:
    # Vérifier que le restaurant existe.
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

    # Le nombre de personnes doit être positif.
    if number_of_people <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le nombre de personnes doit être supérieur à zéro.",
        )

    # Récupérer uniquement les tables disponibles
    # et suffisamment grandes.
    tables = db.execute(
        select(RestaurantTable)
        .where(
            RestaurantTable.restaurant_id == restaurant_id,
            RestaurantTable.capacity >= number_of_people,
            RestaurantTable.status == "available",
        )
        .order_by(
            RestaurantTable.table_number
        )
    ).scalars().all()

    if not tables:
        return AvailabilityResponse(
            restaurant_id=restaurant_id,
            reservation_date=reservation_date,
            reservation_time=reservation_time,
            number_of_people=number_of_people,
            available_tables=[],
        )

    # Récupérer les réservations actives
    # à la date et à l'heure demandées.
    reserved_table_ids = db.execute(
        select(Reservation.table_id)
        .where(
            Reservation.restaurant_id == restaurant_id,
            Reservation.reservation_date == reservation_date,
            Reservation.reservation_time == reservation_time,
            Reservation.status.in_(ACTIVE_RESERVATION_STATUSES),
        )
    ).scalars().all()

    reserved_table_ids = set(reserved_table_ids)

    # Garder uniquement les tables qui ne sont pas réservées.
    available_tables = [
        AvailableTableResponse(
            id=table.id,
            table_number=table.table_number,
            capacity=table.capacity,
        )
        for table in tables
        if table.id not in reserved_table_ids
    ]

    return AvailabilityResponse(
        restaurant_id=restaurant_id,
        reservation_date=reservation_date,
        reservation_time=reservation_time,
        number_of_people=number_of_people,
        available_tables=available_tables,
    )