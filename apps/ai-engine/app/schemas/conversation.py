"""Schémas pour la gestion des conversations et de l'état."""

from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.customer import CustomerContext
from app.schemas.intent import Intent
from app.schemas.reservation import ReservationData, ReservationConfirmation
from app.schemas.availability import AvailabilityResult
from app.schemas.recommendation import RecommendationResult
from app.schemas.payment import PaymentResult
from app.schemas.handoff import HumanHandoffResult


class MessageRole(str, Enum):
    """Rôle de l'auteur d'un message."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    AGENT = "agent"


class Message(BaseModel):
    """Un message dans la conversation."""
    
    model_config = ConfigDict(frozen=True)
    
    role: MessageRole = Field(
        description="Rôle de l'auteur (user, assistant, system, agent)"
    )
    content: str = Field(
        min_length=1,
        description="Contenu du message"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Horodatage du message"
    )
    agent_name: Optional[str] = Field(
        default=None,
        description="Nom de l'agent si role=agent"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Métadonnées additionnelles"
    )


class ConversationContext(BaseModel):
    """Contexte d'une conversation."""
    
    conversation_id: str = Field(
        description="Identifiant unique de la conversation"
    )
    restaurant_id: str = Field(
        description="Identifiant du restaurant (multi-tenant)"
    )
    channel: str = Field(
        description="Canal (chat, whatsapp, sms, voice)"
    )
    customer: Optional[CustomerContext] = Field(
        default=None,
        description="Informations sur le client"
    )
    messages: List[Message] = Field(
        default_factory=list,
        description="Historique des messages"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Date de création"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Dernière mise à jour"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Métadonnées additionnelles"
    )

    def add_message(self, role: MessageRole, content: str, **kwargs) -> None:
        """Ajoute un message à l'historique."""
        message = Message(role=role, content=content, **kwargs)
        self.messages.append(message)
        self.updated_at = datetime.utcnow()

    def get_last_message(self) -> Optional[Message]:
        """Récupère le dernier message."""
        return self.messages[-1] if self.messages else None

    def get_user_messages(self) -> List[Message]:
        """Récupère tous les messages de l'utilisateur."""
        return [m for m in self.messages if m.role == MessageRole.USER]

    def get_assistant_messages(self) -> List[Message]:
        """Récupère tous les messages de l'assistant."""
        return [m for m in self.messages if m.role == MessageRole.ASSISTANT]


class ConversationState(BaseModel):
    """État complet de la conversation pour LangGraph.
    
    C'est le schéma principal qui sera passé entre les nœuds du graphe.
    """
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    # ===== Informations de base =====
    conversation_id: str = Field(
        description="Identifiant unique de la conversation"
    )
    restaurant_id: str = Field(
        description="Identifiant du restaurant"
    )
    channel: str = Field(
        description="Canal (chat, whatsapp, sms, voice)"
    )
    
    # ===== Client =====
    customer: Optional[CustomerContext] = Field(
        default=None,
        description="Informations client"
    )
    
    # ===== Messages =====
    messages: List[Message] = Field(
        default_factory=list,
        description="Historique des messages"
    )
    
    # ===== Intention =====
    intent: Optional[Intent] = Field(
        default=None,
        description="Intention détectée"
    )
    
    # ===== Réservation =====
    reservation: Optional[ReservationData] = Field(
        default=None,
        description="Données de réservation en cours"
    )
    reservation_confirmation: Optional[ReservationConfirmation] = Field(
        default=None,
        description="Confirmation de réservation finale"
    )
    
    # ===== Disponibilité =====
    availability: Optional[AvailabilityResult] = Field(
        default=None,
        description="Résultat de la vérification de disponibilité"
    )
    
    # ===== Recommandation =====
    recommendation: Optional[RecommendationResult] = Field(
        default=None,
        description="Résultat des recommandations"
    )
    
    # ===== Paiement =====
    payment: Optional[PaymentResult] = Field(
        default=None,
        description="Résultat du paiement"
    )
    
    # ===== Transfert humain =====
    handoff: Optional[HumanHandoffResult] = Field(
        default=None,
        description="État du transfert vers un humain"
    )
    
    # ===== Contrôle du workflow =====
    current_agent: Optional[str] = Field(
        default=None,
        description="Agent actuellement actif"
    )
    next_action: Optional[str] = Field(
        default=None,
        description="Prochaine action à effectuer"
    )
    iteration: int = Field(
        default=0,
        ge=0,
        description="Nombre d'itérations effectuées"
    )
    max_iterations: int = Field(
        default=10,
        ge=1,
        description="Nombre maximum d'itérations autorisé"
    )
    
    # ===== Erreurs =====
    error: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Erreur éventuelle"
    )
    error_count: int = Field(
        default=0,
        ge=0,
        description="Nombre d'erreurs consécutives"
    )
    
    # ===== Métadonnées =====
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Métadonnées additionnelles"
    )
    
    # ===== Méthodes utilitaires =====
    
    def add_message(self, role: MessageRole, content: str, **kwargs) -> None:
        """Ajoute un message à l'historique."""
        message = Message(role=role, content=content, **kwargs)
        self.messages.append(message)
    
    def get_last_user_message(self) -> Optional[Message]:
        """Récupère le dernier message de l'utilisateur."""
        for msg in reversed(self.messages):
            if msg.role == MessageRole.USER:
                return msg
        return None
    
    def get_last_assistant_message(self) -> Optional[Message]:
        """Récupère le dernier message de l'assistant."""
        for msg in reversed(self.messages):
            if msg.role == MessageRole.ASSISTANT:
                return msg
        return None
    
    def has_error(self) -> bool:
        """Vérifie si l'état contient une erreur."""
        return self.error is not None
    
    def increment_iteration(self) -> None:
        """Incrémente le nombre d'itérations."""
        self.iteration += 1
    
    def should_handoff(self) -> bool:
        """Vérifie si les conditions de transfert humain sont remplies."""
        if self.handoff and self.handoff.required:
            return True
        if self.error_count >= 3:
            return True
        if self.iteration >= self.max_iterations:
            return True
        return False
    
    def to_conversation_context(self) -> ConversationContext:
        """Convertit en ConversationContext pour la sérialisation."""
        return ConversationContext(
            conversation_id=self.conversation_id,
            restaurant_id=self.restaurant_id,
            channel=self.channel,
            customer=self.customer,
            messages=self.messages,
            metadata=self.metadata,
        )