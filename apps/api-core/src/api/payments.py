from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.enums.role import UserRole
from src.models.restaurant import Restaurant
from src.models.reservation import Reservation
from src.models.user import User
from src.schemas.payment import (
    PaymentCreate,
    PaymentResponse,
    PaymentStatusUpdate,
)
from src.security.auth import get_current_user
from src.services.payment_service import (
    create_payment,
    get_payment,
    get_reservation_payment,
    get_user_payments,
    update_payment_status,
)

router = APIRouter(
    prefix="/payments",
    tags=["Payments"],
)


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_payment_endpoint(
    payment_data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_payment(
        db,
        payment_data,
        str(current_user.id),
    )


@router.get(
    "/me",
    response_model=list[PaymentResponse],
)
def get_my_payments_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_user_payments(
        db,
        str(current_user.id),
    )


@router.get(
    "/reservation/{reservation_id}",
    response_model=PaymentResponse,
)
def get_reservation_payment_endpoint(
    reservation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment = get_reservation_payment(
        db,
        str(reservation_id),
    )

    reservation = db.get(
        Reservation,
        payment.reservation_id,
    )

    if reservation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Réservation introuvable.",
        )

    # Administrateur : accès à tous les paiements
    if current_user.role == UserRole.ADMIN.value:
        return payment

    # Manager : accès uniquement aux paiements
    # des réservations de ses propres restaurants
    if current_user.role == UserRole.MANAGER.value:
        restaurant = db.get(
            Restaurant,
            reservation.restaurant_id,
        )

        if (
            restaurant is None
            or restaurant.manager_id != str(current_user.id)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès interdit à ce paiement.",
            )

        return payment

    # Client : accès uniquement à son propre paiement
    if reservation.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès interdit à ce paiement.",
        )

    return payment


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
)
def get_payment_endpoint(
    payment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payment = get_payment(
        db,
        str(payment_id),
    )

    reservation = db.get(
        Reservation,
        payment.reservation_id,
    )

    if reservation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Réservation introuvable.",
        )

    # Administrateur : accès à tous les paiements
    if current_user.role == UserRole.ADMIN.value:
        return payment

    # Manager : accès uniquement aux paiements
    # des réservations de ses propres restaurants
    if current_user.role == UserRole.MANAGER.value:
        restaurant = db.get(
            Restaurant,
            reservation.restaurant_id,
        )

        if (
            restaurant is None
            or restaurant.manager_id != str(current_user.id)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès interdit à ce paiement.",
            )

        return payment

    # Client : accès uniquement à son propre paiement
    if reservation.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès interdit à ce paiement.",
        )

    return payment


@router.patch(
    "/{payment_id}/status",
    response_model=PaymentResponse,
)
def update_payment_status_endpoint(
    payment_id: UUID,
    status_data: PaymentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Seuls les administrateurs et managers peuvent
    # modifier le statut d'un paiement.
    if current_user.role not in {
        UserRole.ADMIN.value,
        UserRole.MANAGER.value,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs et aux managers.",
        )

    payment = get_payment(
        db,
        str(payment_id),
    )

    reservation = db.get(
        Reservation,
        payment.reservation_id,
    )

    if reservation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Réservation introuvable.",
        )

    # Un manager ne peut modifier que les paiements
    # liés à ses propres restaurants.
    if current_user.role == UserRole.MANAGER.value:
        restaurant = db.get(
            Restaurant,
            reservation.restaurant_id,
        )

        if (
            restaurant is None
            or restaurant.manager_id != str(current_user.id)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès interdit à ce paiement.",
            )

    return update_payment_status(
        db,
        str(payment_id),
        status_data,
    )