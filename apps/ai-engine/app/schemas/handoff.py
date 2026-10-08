"""Schémas pour le transfert vers un humain."""

from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class HandoffReason(str, Enum):
    """Raisons du transfert vers un humain."""
    REQUESTED_BY_USER = "requested_by_user"
    TOO_COMPLEX = "too_complex"
    REPEATED_MISUNDERSTANDING = "repeated_misunderstanding"
    CRITICAL_OPERATION_FAILED = "critical_operation_failed"
    PAYMENT_ISSUE = "payment_issue"
    RESERVATION_CONFLICT = "reservation_conflict"
    OUT_OF_SCOPE = "out_of_scope"
    SYSTEM_ERROR = "system_error"


class HumanHandoffRequest(BaseModel):
    """Requête de transfert vers un humain."""
    
    conversation_id: str = Field(
        description="ID de la conversation"
    )
    restaurant_id: str = Field(
        description="ID du restaurant"
    )
    reason: HandoffReason = Field(
        description="Raison du transfert"
    )
    summary: str = Field(
        description="Résumé de la conversation"
    )
    collected_data: dict = Field(
        default_factory=dict,
        description="Données collectées"
    )
    pending_action: Optional[str] = Field(
        default=None,
        description="Action en attente"
    )
    urgency_level: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Niveau d'urgence (1 = faible, 5 = critique)"
    )


class HumanHandoffResult(BaseModel):
    """Résultat du transfert vers un humain."""
    
    required: bool = Field(
        description="Un transfert est-il nécessaire ?"
    )
    reason: Optional[HandoffReason] = Field(
        default=None,
        description="Raison du transfert"
    )
    message: str = Field(
        description="Message à afficher à l'utilisateur"
    )
    handoff_id: Optional[str] = Field(
        default=None,
        description="ID de la demande de transfert"
    )
    summary: Optional[str] = Field(
        default=None,
        description="Résumé de la conversation pour le personnel"
    )
    triggered_at: Optional[str] = Field(
        default=None,
        description="Date de déclenchement"
    )
    
    @classmethod
    def create_handoff(
        cls,
        reason: HandoffReason,
        message: str,
        summary: str,
    ) -> "HumanHandoffResult":
        """Crée un résultat de transfert."""
        return cls(
            required=True,
            reason=reason,
            message=message,
            summary=summary,
        )
    
    @classmethod
    def no_handoff(cls) -> "HumanHandoffResult":
        """Crée un résultat sans transfert."""
        return cls(
            required=False,
            message="Pas de transfert humain nécessaire",
        )