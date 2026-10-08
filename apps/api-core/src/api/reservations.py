from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.enums.role import UserRole
from src.models.notification import Notification
from src.models.user import User
from src.schemas.reservation import (
    ReservationCreate,
    ReservationResponse,
    ReservationStatusUpdate,
    ReservationUpdate,
)
from src.security.auth import get_current_user
from src.services.reservation_service import (
    create_reservation,
    delete_reservation,
    get_manager_reservation,
    get_manager_reservations,
    get_reservation,
    get_reservations,
    get_user_reservations,
    update_reservation,
)


router = APIRouter(
    prefix="/reservations",
    tags=["Reservations"],
)


# ============================================================
# CRÉER UNE RÉSERVATION
# CLIENT UNIQUEMENT
# ============================================================

@router.post(
    "",
    response_model=ReservationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_reservation_endpoint(
    reservation_data: ReservationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.CLIENT.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les clients peuvent créer une réservation.",
        )

    return create_reservation(
        db,
        str(current_user.id),
        reservation_data,
    )


# ============================================================
# VOIR LES RÉSERVATIONS
#
# ADMIN   → TOUTES
# MANAGER → SES RESTAURANTS
# CLIENT  → 403
# ============================================================

@router.get(
    "",
    response_model=list[ReservationResponse],
)
def get_reservations_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.ADMIN.value:
        return get_reservations(db)

    if current_user.role == UserRole.MANAGER.value:
        return get_manager_reservations(
            db,
            str(current_user.id),
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Accès réservé aux administrateurs et aux managers.",
    )


# ============================================================
# VOIR MES RÉSERVATIONS
# ============================================================

@router.get(
    "/me",
    response_model=list[ReservationResponse],
)
def get_my_reservations_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_user_reservations(
        db,
        str(current_user.id),
    )


# ============================================================
# VOIR UNE RÉSERVATION
# ============================================================

@router.get(
    "/{reservation_id}",
    response_model=ReservationResponse,
)
def get_reservation_endpoint(
    reservation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reservation_id_str = str(reservation_id)

    # ADMIN
    if current_user.role == UserRole.ADMIN.value:
        return get_reservation(
            db,
            reservation_id_str,
        )

    # MANAGER
    if current_user.role == UserRole.MANAGER.value:
        return get_manager_reservation(
            db,
            reservation_id_str,
            str(current_user.id),
        )

    # CLIENT
    reservation = get_reservation(
        db,
        reservation_id_str,
    )

    if str(current_user.id) != str(reservation.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à consulter cette réservation.",
        )

    return reservation


# ============================================================
# MODIFIER UNE RÉSERVATION
# ============================================================

@router.put(
    "/{reservation_id}",
    response_model=ReservationResponse,
)
def update_reservation_endpoint(
    reservation_id: UUID,
    reservation_data: ReservationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reservation_id_str = str(reservation_id)

    # ADMIN
    if current_user.role == UserRole.ADMIN.value:
        return update_reservation(
            db,
            reservation_id_str,
            reservation_data,
        )

    # MANAGER
    if current_user.role == UserRole.MANAGER.value:
        get_manager_reservation(
            db,
            reservation_id_str,
            str(current_user.id),
        )

        return update_reservation(
            db,
            reservation_id_str,
            reservation_data,
        )

    # CLIENT
    reservation = get_reservation(
        db,
        reservation_id_str,
    )

    if str(current_user.id) != str(reservation.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à modifier cette réservation.",
        )

    return update_reservation(
        db,
        reservation_id_str,
        reservation_data,
    )


# ============================================================
# MODIFIER LE STATUT
#
# ADMIN + MANAGER
#
# pending   → confirmed
# pending   → cancelled
# confirmed → cancelled
#
# Une notification est créée pour le client.
# ============================================================

@router.patch(
    "/{reservation_id}/status",
    response_model=ReservationResponse,
)
def update_reservation_status_endpoint(
    reservation_id: UUID,
    status_data: ReservationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reservation_id_str = str(reservation_id)

    allowed_statuses = [
        "pending",
        "confirmed",
        "cancelled",
    ]

    # Vérification du statut demandé
    if status_data.status not in allowed_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Statut invalide. "
                "Utilisez pending, confirmed ou cancelled."
            ),
        )

    # ========================================================
    # VÉRIFICATION DES AUTORISATIONS
    # ========================================================

    # ADMIN → peut modifier n'importe quelle réservation
    if current_user.role == UserRole.ADMIN.value:
        reservation = get_reservation(
            db,
            reservation_id_str,
        )

    # MANAGER → uniquement les réservations de son restaurant
    elif current_user.role == UserRole.MANAGER.value:
        reservation = get_manager_reservation(
            db,
            reservation_id_str,
            str(current_user.id),
        )

    # CLIENT → interdit
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Seuls les administrateurs et les managers "
                "peuvent modifier le statut."
            ),
        )

    # ========================================================
    # CONFIRMER UNE RÉSERVATION
    # ========================================================

    if status_data.status == "confirmed":

        if reservation.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Seules les réservations en attente "
                    "peuvent être confirmées."
                ),
            )

        reservation.status = "confirmed"

        notification = Notification(
            user_id=str(reservation.user_id),
            title="Réservation confirmée",
            message="Votre réservation a été confirmée.",
            type="reservation_confirmed",
        )

        db.add(notification)

    # ========================================================
    # ANNULER UNE RÉSERVATION
    # ========================================================

    elif status_data.status == "cancelled":

        if reservation.status == "cancelled":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cette réservation est déjà annulée.",
            )

        reservation.status = "cancelled"

        notification = Notification(
            user_id=str(reservation.user_id),
            title="Réservation annulée",
            message="Votre réservation a été annulée.",
            type="reservation_cancelled",
        )

        db.add(notification)

    # ========================================================
    # REMETTRE UNE RÉSERVATION EN ATTENTE
    # ========================================================

    elif status_data.status == "pending":

        reservation.status = "pending"

    # ========================================================
    # SAUVEGARDE
    # ========================================================

    db.commit()
    db.refresh(reservation)

    return reservation


# ============================================================
# SUPPRIMER UNE RÉSERVATION
# ============================================================

@router.delete(
    "/{reservation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_reservation_endpoint(
    reservation_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reservation_id_str = str(reservation_id)

    # ADMIN
    if current_user.role == UserRole.ADMIN.value:
        delete_reservation(
            db,
            reservation_id_str,
        )
        return None

    # MANAGER
    if current_user.role == UserRole.MANAGER.value:
        get_manager_reservation(
            db,
            reservation_id_str,
            str(current_user.id),
        )

        delete_reservation(
            db,
            reservation_id_str,
        )
        return None

    # CLIENT
    reservation = get_reservation(
        db,
        reservation_id_str,
    )

    if str(current_user.id) != str(reservation.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous n'êtes pas autorisé à supprimer cette réservation.",
        )

    delete_reservation(
        db,
        reservation_id_str,
    )

    return None