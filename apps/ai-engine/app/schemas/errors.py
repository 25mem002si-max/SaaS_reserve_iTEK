"""Schémas pour les erreurs des agents."""

from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class ErrorType(str, Enum):
    """Types d'erreurs possibles."""
    # Erreurs backend
    BACKEND_UNAVAILABLE = "backend_unavailable"
    BACKEND_TIMEOUT = "backend_timeout"
    BACKEND_ERROR = "backend_error"
    
    # Erreurs de disponibilité
    NO_TABLES_AVAILABLE = "no_tables_available"
    TABLE_LOCK_FAILED = "table_lock_failed"
    TABLE_ALREADY_RESERVED = "table_already_reserved"
    
    # Erreurs de réservation
    RESERVATION_CREATION_FAILED = "reservation_creation_failed"
    RESERVATION_NOT_FOUND = "reservation_not_found"
    
    # Erreurs de paiement
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_TIMEOUT = "payment_timeout"
    INSUFFICIENT_FUNDS = "insufficient_funds"
    
    # Erreurs LLM
    LLM_ERROR = "llm_error"
    LLM_TIMEOUT = "llm_timeout"
    LLM_INVALID_RESPONSE = "llm_invalid_response"
    
    # Erreurs de validation
    VALIDATION_ERROR = "validation_error"
    MISSING_INFORMATION = "missing_information"
    
    # Erreurs système
    SYSTEM_ERROR = "system_error"
    UNKNOWN_ERROR = "unknown_error"


class AgentError(BaseModel):
    """Erreur survenue dans un agent."""
    
    error_type: ErrorType = Field(
        description="Type d'erreur"
    )
    message: str = Field(
        description="Message d'erreur"
    )
    agent_name: str = Field(
        description="Nom de l'agent ayant généré l'erreur"
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Détails supplémentaires"
    )
    original_error: Optional[str] = Field(
        default=None,
        description="Erreur originale"
    )
    
    def to_user_message(self) -> str:
        """Convertit l'erreur en message utilisateur."""
        user_messages = {
            ErrorType.NO_TABLES_AVAILABLE: "Je suis désolé, aucune table n'est disponible pour ce créneau. Voulez-vous vérifier un autre horaire ?",
            ErrorType.TABLE_LOCK_FAILED: "Cette table vient d'être réservée par un autre client. Puis-je vous proposer un autre créneau ?",
            ErrorType.PAYMENT_FAILED: "Le paiement n'a pas pu être traité. Voulez-vous réessayer ou contacter le restaurant directement ?",
            ErrorType.BACKEND_UNAVAILABLE: "Je rencontre des difficultés techniques. Veuillez patienter ou nous contacter directement.",
            ErrorType.LLM_ERROR: "Je n'ai pas bien compris. Pouvez-vous reformuler votre demande ?",
        }
        return user_messages.get(self.error_type, self.message)


class ToolError(BaseModel):
    """Erreur survenue dans un tool/function call."""
    
    tool_name: str = Field(
        description="Nom du tool ayant échoué"
    )
    error_type: ErrorType = Field(
        description="Type d'erreur"
    )
    message: str = Field(
        description="Message d'erreur"
    )
    input_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Données d'entrée du tool"
    )
    retryable: bool = Field(
        default=True,
        description="L'erreur est-elle réessayable ?"
    )