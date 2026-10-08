from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.dependencies import get_db
from src.enums.role import UserRole
from src.models.user import User
from src.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
)
from src.security.auth import get_current_admin, get_current_user
from src.services.notification_service import (
    create_notification,
    delete_notification,
    get_notification,
    get_user_notifications,
    mark_notification_as_read,
)

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.post(
    "",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_notification_endpoint(
    notification_data: NotificationCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """
    Crée une notification.

    Seul un administrateur peut créer une notification.
    """
    return create_notification(
        db,
        notification_data,
    )


@router.get(
    "/me",
    response_model=list[NotificationResponse],
)
def get_my_notifications_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retourne uniquement les notifications de l'utilisateur connecté.
    """
    return get_user_notifications(
        db,
        current_user.id,
    )


@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
)
def get_notification_endpoint(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retourne une notification.

    Un utilisateur peut consulter sa propre notification.
    Un administrateur peut consulter n'importe quelle notification.
    """
    notification = get_notification(
        db,
        str(notification_id),
    )

    if (
        notification.user_id != current_user.id
        and current_user.role != UserRole.ADMIN.value
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès interdit à cette notification.",
        )

    return notification


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
)
def mark_notification_as_read_endpoint(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Marque une notification comme lue.

    Un utilisateur ne peut modifier que sa propre notification.
    """
    return mark_notification_as_read(
        db,
        str(notification_id),
        current_user.id,
    )


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_notification_endpoint(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Supprime une notification appartenant à l'utilisateur connecté.
    """
    delete_notification(
        db,
        str(notification_id),
        current_user.id,
    )

    return None