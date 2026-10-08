"""Schémas pour les notifications."""

from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class NotificationType(str, Enum):
    """Types de notifications."""
    CONFIRMATION = "confirmation"
    REMINDER_24H = "reminder_24h"
    REMINDER_2H = "reminder_2h"
    PAYMENT_RECEIVED = "payment_received"
    RESERVATION_CANCELLED = "reservation_cancelled"
    WAITING_LIST_AVAILABLE = "waiting_list_available"
    HUMAN_HANDOFF = "human_handoff"


class NotificationChannel(str, Enum):
    """Canaux de notification."""
    WHATSAPP = "whatsapp"
    SMS = "sms"
    EMAIL = "email"
    CHAT = "chat"


class NotificationRequest(BaseModel):
    """Requête de notification."""
    
    type: NotificationType = Field(
        description="Type de notification"
    )
    recipient: str = Field(
        description="Destinataire (téléphone, email, etc.)"
    )
    channel: NotificationChannel = Field(
        default=NotificationChannel.WHATSAPP,
        description="Canal de notification"
    )
    restaurant_id: str = Field(
        description="ID du restaurant"
    )
    reservation_id: str = Field(
        description="ID de la réservation"
    )
    template_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Données pour le template"
    )
    attachments: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Pièces jointes (PDF, etc.)"
    )
    priority: int = Field(
        default=0,
        ge=0,
        le=10,
        description="Priorité de la notification"
    )


class NotificationResult(BaseModel):
    """Résultat d'une notification."""
    
    notification_id: str = Field(
        description="ID de la notification"
    )
    type: NotificationType = Field(
        description="Type de notification"
    )
    channel: NotificationChannel = Field(
        description="Canal utilisé"
    )
    sent: bool = Field(
        description="La notification a-t-elle été envoyée ?"
    )
    sent_at: Optional[str] = Field(
        default=None,
        description="Date d'envoi"
    )
    error: Optional[str] = Field(
        default=None,
        description="Erreur éventuelle"
    )
    message: str = Field(
        description="Message de confirmation"
    )