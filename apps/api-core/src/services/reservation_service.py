from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.reservation import Reservation
from src.models.restaurant import Restaurant
from src.models.restaurant_table import RestaurantTable
from src.models.user import User
from src.schemas.reservation import ReservationCreate, ReservationUpdate


ACTIVE_RESERVATION_STATUSES = {
    "pending",
    "confirmed",
}


def create_reservation(
    db: Session,
    user_id: str,
    reservation_data: ReservationCreate,
) -> Reservation:
    restaurant = db.execute(
        select(Restaurant).where(
            Restaurant.id == str(reservation_data.restaurant_id)
        )
    ).scalar_one_or_none()

    if restaurant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Restaurant introuvable.",
        )

    table = db.execute(
        select(RestaurantTable).where(
            RestaurantTable.id == str(reservation_data.table_id)
        )
    ).scalar_one_or_none()

    if table is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table introuvable.",
        )

    if table.restaurant_id != str(reservation_data.restaurant_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cette table n'appartient pas à ce restaurant.",
        )

    # Une table doit être disponible pour pouvoir être réservée.
    if table.status != "available":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cette table n'est pas disponible pour une réservation.",
        )

    if reservation_data.number_of_people <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le nombre de personnes doit être supérieur à zéro.",
        )

    if reservation_data.number_of_people > table.capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le nombre de personnes dépasse la capacité de la table.",
        )

    user = db.execute(
        select(User).where(
            User.id == user_id
        )
    ).scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur introuvable.",
        )

    existing_reservation = db.execute(
        select(Reservation).where(
            Reservation.table_id == str(reservation_data.table_id),
            Reservation.reservation_date == reservation_data.reservation_date,
            Reservation.reservation_time == reservation_data.reservation_time,
            Reservation.status.in_(ACTIVE_RESERVATION_STATUSES),
        )
    ).scalar_one_or_none()

    if existing_reservation is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cette table est déjà réservée à cette date et cette heure.",
        )

    reservation = Reservation(
        restaurant_id=str(reservation_data.restaurant_id),
        table_id=str(reservation_data.table_id),
        user_id=user_id,
        reservation_date=reservation_data.reservation_date,
        reservation_time=reservation_data.reservation_time,
        number_of_people=reservation_data.number_of_people,
        status="pending",
    )

    db.add(reservation)
    db.commit()
    db.refresh(reservation)

    return reservation


def get_reservations(
    db: Session,
) -> list[Reservation]:
    result = db.execute(
        select(Reservation)
    )

    return result.scalars().all()


def get_manager_reservations(
    db: Session,
    manager_id: str,
) -> list[Reservation]:
    result = db.execute(
        select(Reservation)
        .join(
            Restaurant,
            Restaurant.id == Reservation.restaurant_id,
        )
        .where(
            Restaurant.manager_id == manager_id
        )
    )

    return result.scalars().all()


def get_reservation(
    db: Session,
    reservation_id: str,
) -> Reservation:
    reservation = db.execute(
        select(Reservation).where(
            Reservation.id == reservation_id
        )
    ).scalar_one_or_none()

    if reservation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Réservation introuvable.",
        )

    return reservation


def get_manager_reservation(
    db: Session,
    reservation_id: str,
    manager_id: str,
) -> Reservation:
    reservation = db.execute(
        select(Reservation)
        .join(
            Restaurant,
            Restaurant.id == Reservation.restaurant_id,
        )
        .where(
            Reservation.id == reservation_id,
            Restaurant.manager_id == manager_id,
        )
    ).scalar_one_or_none()

    if reservation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Réservation introuvable ou non attribuée à ce manager.",
        )

    return reservation


def get_user_reservations(
    db: Session,
    user_id: str,
) -> list[Reservation]:
    result = db.execute(
        select(Reservation).where(
            Reservation.user_id == user_id
        )
    )

    return result.scalars().all()


def update_reservation(
    db: Session,
    reservation_id: str,
    reservation_data: ReservationUpdate,
) -> Reservation:
    reservation = get_reservation(
        db,
        reservation_id,
    )

    new_date = (
        reservation_data.reservation_date
        if reservation_data.reservation_date is not None
        else reservation.reservation_date
    )

    new_time = (
        reservation_data.reservation_time
        if reservation_data.reservation_time is not None
        else reservation.reservation_time
    )

    new_people = (
        reservation_data.number_of_people
        if reservation_data.number_of_people is not None
        else reservation.number_of_people
    )

    if new_people <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le nombre de personnes doit être supérieur à zéro.",
        )

    table = db.execute(
        select(RestaurantTable).where(
            RestaurantTable.id == reservation.table_id
        )
    ).scalar_one_or_none()

    if table is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Table introuvable.",
        )

    if new_people > table.capacity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le nombre de personnes dépasse la capacité de la table.",
        )

    conflicting_reservation = db.execute(
        select(Reservation).where(
            Reservation.table_id == reservation.table_id,
            Reservation.reservation_date == new_date,
            Reservation.reservation_time == new_time,
            Reservation.status.in_(ACTIVE_RESERVATION_STATUSES),
            Reservation.id != reservation.id,
        )
    ).scalar_one_or_none()

    if conflicting_reservation is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cette table est déjà réservée à cette date et cette heure.",
        )

    reservation.reservation_date = new_date
    reservation.reservation_time = new_time
    reservation.number_of_people = new_people

    db.commit()
    db.refresh(reservation)

    return reservation


def delete_reservation(
    db: Session,
    reservation_id: str,
) -> None:
    reservation = get_reservation(
        db,
        reservation_id,
    )

    db.delete(reservation)
    db.commit()
def confirm_reservation(
    db: Session,
    reservation_id: str,
) -> Reservation:
    reservation = get_reservation(db, reservation_id)

    if reservation.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seules les réservations en attente peuvent être confirmées.",
        )

    reservation.status = "confirmed"

    db.commit()
    db.refresh(reservation)

    return reservation


def cancel_reservation(
    db: Session,
    reservation_id: str,
) -> Reservation:
    reservation = get_reservation(db, reservation_id)

    if reservation.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cette réservation est déjà annulée.",
        )

    reservation.status = "cancelled"

    db.commit()
    db.refresh(reservation)

    return reservation