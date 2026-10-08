"""Définition de l'état conversationnel pour LangGraph."""

from typing import Optional, List, Dict, Any, Literal, Annotated
from datetime import datetime
from typing_extensions import TypedDict

from app.schemas.conversation import Message, MessageRole
from app.schemas.customer import CustomerContext
from app.schemas.intent import Intent
from app.schemas.nlp import ExtractedInformation, NLPResult
from app.schemas.reservation import ReservationData, ReservationConfirmation
from app.schemas.availability import AvailabilityResult, TableOption
from app.schemas.recommendation import RecommendationResult
from app.schemas.payment import PaymentResult
from app.schemas.handoff import HumanHandoffResult, HandoffReason
from app.schemas.errors import AgentError, ErrorType


def add_messages(left: List[Message], right: List[Message]) -> List[Message]:
    """Fonction de réduction pour les messages."""
    return left + right


def add_metadata(left: Dict[str, Any], right: Dict[str, Any]) -> Dict[str, Any]:
    """Fonction de réduction pour les métadonnées."""
    result = left.copy()
    result.update(right)
    return result


class ConversationState(TypedDict, total=False):
    """État complet de la conversation pour LangGraph."""
    
    conversation_id: str
    restaurant_id: str
    channel: Literal["chat", "whatsapp", "sms", "voice"]
    
    messages: Annotated[List[Message], add_messages]
    
    customer: Optional[CustomerContext]
    
    intent: Optional[Intent]
    
    extracted_info: Optional[ExtractedInformation]
    nlp_result: Optional[NLPResult]
    
    reservation: Optional[ReservationData]
    reservation_confirmation: Optional[ReservationConfirmation]
    
    availability: Optional[AvailabilityResult]
    selected_table: Optional[TableOption]
    
    recommendation: Optional[RecommendationResult]
    
    payment: Optional[PaymentResult]
    payment_required: bool
    
    handoff: Optional[HumanHandoffResult]
    handoff_reason: Optional[HandoffReason]
    
    current_agent: Optional[str]
    next_action: Optional[str]
    iteration: int
    max_iterations: int
    
    error: Optional[AgentError]  # ← Utiliser AgentError, pas str
    error_count: int
    retry_count: int
    
    metadata: Annotated[Dict[str, Any], add_metadata]
    conversation_summary: Optional[str]
    requires_clarification: bool
    clarification_question: Optional[str]
    message: Optional[str]
    is_complete: bool
    waiting_for_payment: bool
    lock_token: Optional[str]


def create_initial_state(
    conversation_id: str,
    restaurant_id: str,
    channel: str = "chat",
    customer: Optional[CustomerContext] = None,
    max_iterations: int = 10,
) -> ConversationState:
    """Crée un état initial pour une nouvelle conversation."""
    
    return {
        "conversation_id": conversation_id,
        "restaurant_id": restaurant_id,
        "channel": channel,
        "messages": [],
        "customer": customer,
        "intent": None,
        "extracted_info": None,
        "nlp_result": None,
        "reservation": None,
        "reservation_confirmation": None,
        "availability": None,
        "selected_table": None,
        "recommendation": None,
        "payment": None,
        "payment_required": False,
        "handoff": None,
        "handoff_reason": None,
        "current_agent": None,
        "next_action": None,
        "iteration": 0,
        "max_iterations": max_iterations,
        "error": None,
        "error_count": 0,
        "retry_count": 0,
        "metadata": {},
        "conversation_summary": None,
        "requires_clarification": False,
        "clarification_question": None,
        "is_complete": False,
        "waiting_for_payment": False,
        "lock_token": None,
    }


def get_last_user_message(state: ConversationState) -> Optional[str]:
    """Récupère le dernier message de l'utilisateur."""
    messages = state.get("messages", [])
    for msg in reversed(messages):
        if msg.role == MessageRole.USER:
            return msg.content
    return None


def get_last_assistant_message(state: ConversationState) -> Optional[str]:
    """Récupère le dernier message de l'assistant."""
    messages = state.get("messages", [])
    for msg in reversed(messages):
        if msg.role == MessageRole.ASSISTANT:
            return msg.content
    return None


def add_user_message(state: ConversationState, content: str) -> ConversationState:
    """Ajoute un message utilisateur à l'état."""
    messages = state.get("messages", [])
    messages.append(Message(role=MessageRole.USER, content=content))
    state["messages"] = messages
    state["iteration"] = state.get("iteration", 0) + 1
    return state


def add_assistant_message(state: ConversationState, content: str) -> ConversationState:
    """Ajoute un message assistant à l'état."""
    messages = state.get("messages", [])
    messages.append(Message(role=MessageRole.ASSISTANT, content=content))
    state["messages"] = messages
    return state


def should_handoff(state: ConversationState) -> bool:
    """Vérifie si les conditions de transfert humain sont remplies."""
    
    # 1. Transfert explicitement demandé
    if state.get("handoff") and state["handoff"].required:
        return True
    
    # 2. Trop d'erreurs
    if state.get("error_count", 0) >= 3:
        return True
    
    # 3. Trop d'itérations
    if state.get("iteration", 0) >= state.get("max_iterations", 10):
        return True
    
    # 4. Erreur critique - CORRECTION : vérifier si error est un AgentError
    error = state.get("error")
    if error is not None:
        # Si error est un AgentError, vérifier son type
        if hasattr(error, "error_type"):
            if error.error_type in [
                ErrorType.SYSTEM_ERROR,
                ErrorType.BACKEND_UNAVAILABLE,
            ]:
                return True
        # Les erreurs métier sont retournées par les agents sous forme de texte.
        # Elles ne doivent pas interrompre toute la conversation après un seul échec.
    
    return False


def is_reservation_ready(state: ConversationState) -> bool:
    """Vérifie si toutes les données de réservation sont prêtes."""
    reservation = state.get("reservation")
    if not reservation:
        return False
    return reservation.is_complete()


def is_payment_required(state: ConversationState) -> bool:
    """Vérifie si un paiement est requis."""
    if state.get("payment_required", False):
        return True
    reservation = state.get("reservation")
    if reservation and reservation.deposit_required:
        return True
    return False


def get_handoff_summary(state: ConversationState) -> str:
    """Génère un résumé de la conversation pour le transfert humain."""
    lines = []
    
    customer = state.get("customer")
    if customer:
        lines.append(f"👤 Client: {customer.name or 'Non renseigné'}")
        lines.append(f"📱 Téléphone: {customer.phone or 'Non renseigné'}")
    
    reservation = state.get("reservation")
    if reservation:
        lines.append(f"📅 Date: {reservation.date}")
        lines.append(f"⏰ Heure: {reservation.time}")
        lines.append(f"👥 Couverts: {reservation.guests_count}")
        if reservation.table_label:
            lines.append(f"📍 Table: {reservation.table_label}")
    
    messages = state.get("messages", [])
    lines.append(f"\n💬 Derniers messages:")
    for msg in messages[-5:]:
        prefix = "👤 Client" if msg.role == MessageRole.USER else "🤖 IA"
        lines.append(f"  {prefix}: {msg.content}")
    
    return "\n".join(lines)