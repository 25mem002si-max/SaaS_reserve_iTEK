"""Schémas pour la détection d'intention."""

from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class IntentType(str, Enum):
    """Types d'intentions détectées."""
    
    # Réservation
    NEW_RESERVATION = "new_reservation"
    CHECK_AVAILABILITY = "check_availability"
    MODIFY_RESERVATION = "modify_reservation"
    CANCEL_RESERVATION = "cancel_reservation"
    
    # Recommandation
    GET_RECOMMENDATIONS = "get_recommendations"
    
    # Paiement
    PAYMENT = "payment"
    
    # Communication
    GREETING = "greeting"
    GOODBYE = "goodbye"
    CHITCHAT = "chitchat"
    
    # Support
    HUMAN_HANDOFF = "human_handoff"
    
    # Autre
    UNKNOWN = "unknown"


class Intent(BaseModel):
    """Intention détectée dans le message de l'utilisateur."""
    
    type: IntentType = Field(
        description="Type d'intention détectée"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Niveau de confiance (0.0 à 1.0)"
    )
    alternative_intents: List[IntentType] = Field(
        default_factory=list,
        description="Intentions alternatives possibles"
    )
    requires_clarification: bool = Field(
        default=False,
        description="Nécessite une clarification"
    )
    clarification_question: Optional[str] = Field(
        default=None,
        description="Question de clarification si nécessaire"
    )
    
    def is_reservation_intent(self) -> bool:
        """Vérifie si l'intention est liée à une réservation."""
        return self.type in [
            IntentType.NEW_RESERVATION,
            IntentType.CHECK_AVAILABILITY,
            IntentType.MODIFY_RESERVATION,
            IntentType.CANCEL_RESERVATION,
        ]
    
    def requires_payment(self) -> bool:
        """Vérifie si l'intention nécessite un paiement."""
        return self.type == IntentType.PAYMENT
    
    def is_handoff(self) -> bool:
        """Vérifie si l'intention est un transfert humain."""
        return self.type == IntentType.HUMAN_HANDOFF