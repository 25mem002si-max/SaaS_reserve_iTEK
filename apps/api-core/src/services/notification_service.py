from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models.notification import Notification
from src.schemas.notification import NotificationCreate


def create_notification(
    db: Session,
    notification_data: NotificationCreate,
):
    notification = Notification(
        user_id=str(notification_data.user_id),
        title=notification_data.title,
        message=notification_data.message,
        type=notification_data.type,
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification


def get_user_notifications(
    db: Session,
    user_id: str,
):
    result = db.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
    )

    return result.scalars().all()


def get_notification(
    db: Session,
    notification_id: str,
):
    notification = db.execute(
        select(Notification).where(
            Notification.id == notification_id
        )
    ).scalar_one_or_none()

    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification introuvable.",
        )

    return notification


def mark_notification_as_read(
    db: Session,
    notification_id: str,
    user_id: str,
):
    notification = db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    ).scalar_one_or_none()

    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification introuvable.",
        )

    notification.is_read = True

    db.commit()
    db.refresh(notification)

    return notification


def delete_notification(
    db: Session,
    notification_id: str,
    user_id: str,
):
    notification = db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    ).scalar_one_or_none()

    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification introuvable.",
        )

    db.delete(notification)
    db.commit()