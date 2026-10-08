from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.payment import Payment
from src.models.reservation import Reservation
from src.schemas.payment import PaymentCreate, PaymentStatusUpdate


ALLOWED_PAYMENT_STATUSES = {
    "pending",
    "paid",
    "failed",
    "cancelled",
}


def create_payment(
    db: Session,
    payment_data: PaymentCreate,
    user_id: str,
) -> Payment:
    reservation = db.execute(
        select(Reservation).where(
            Reservation.id == str(payment_data.reservation_id)
        )
    ).scalar_one_or_none()

    if reservation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Réservation introuvable.",
        )

    # Le client ne peut payer que sa propre réservation.
    if reservation.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès interdit à cette réservation.",
        )

    # Une réservation annulée ne peut pas être payée.
    if reservation.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Une réservation annulée ne peut pas être payée.",
        )

    # Le montant doit être strictement positif.
    if payment_data.amount <= Decimal("0"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le montant doit être supérieur à zéro.",
        )

    # Une réservation ne peut avoir qu'un seul paiement.
    existing_payment = db.execute(
        select(Payment).where(
            Payment.reservation_id == str(payment_data.reservation_id)
        )
    ).scalar_one_or_none()

    if existing_payment is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un paiement existe déjà pour cette réservation.",
        )

    payment = Payment(
        reservation_id=str(payment_data.reservation_id),
        amount=payment_data.amount,
        currency=payment_data.currency,
        payment_method=payment_data.payment_method,
        status="pending",
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    return payment


def get_payment(
    db: Session,
    payment_id: str,
) -> Payment:
    payment = db.execute(
        select(Payment).where(
            Payment.id == payment_id
        )
    ).scalar_one_or_none()

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paiement introuvable.",
        )

    return payment


def get_reservation_payment(
    db: Session,
    reservation_id: str,
) -> Payment:
    payment = db.execute(
        select(Payment).where(
            Payment.reservation_id == reservation_id
        )
    ).scalar_one_or_none()

    if payment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paiement introuvable.",
        )

    return payment


def get_user_payments(
    db: Session,
    user_id: str,
) -> list[Payment]:
    result = db.execute(
        select(Payment)
        .join(
            Reservation,
            Payment.reservation_id == Reservation.id,
        )
        .where(
            Reservation.user_id == user_id
        )
        .order_by(
            Payment.created_at.desc()
        )
    )

    return result.scalars().all()


def update_payment_status(
    db: Session,
    payment_id: str,
    status_data: PaymentStatusUpdate,
) -> Payment:
    payment = get_payment(
        db,
        payment_id,
    )

    if status_data.status not in ALLOWED_PAYMENT_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Statut de paiement invalide.",
        )

    current_status = payment.status
    new_status = status_data.status

    # Un paiement déjà finalisé ne peut plus changer de statut.
    if current_status in {"paid", "failed", "cancelled"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le statut de ce paiement ne peut plus être modifié.",
        )

    payment.status = new_status

    if status_data.transaction_id is not None:
        payment.transaction_id = status_data.transaction_id

    db.commit()
    db.refresh(payment)

    return payment