"""Schémas Pydantic pour l'AI Engine.

Ce module exporte tous les schémas utilisés par le système.
"""

from app.schemas.conversation import (
    ConversationState,
    ConversationContext,
    Message,
    MessageRole,
)
from app.schemas.customer import CustomerContext
from app.schemas.intent import Intent, IntentType
from app.schemas.nlp import ExtractedInformation, MissingInformation, NLPResult
from app.schemas.reservation import (
    ReservationRequest,
    ReservationData,
    ReservationConfirmation,
    ReservationStatus,
)
from app.schemas.availability import (
    AvailabilityRequest,
    AvailabilityResult,
    TableOption,
    TableStatus,
)
from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResult,
    RecommendedItem,
)
from app.schemas.payment import PaymentRequest, PaymentResult, PaymentStatus
from app.schemas.notification import NotificationRequest, NotificationResult
from app.schemas.handoff import HumanHandoffRequest, HumanHandoffResult
from app.schemas.errors import AgentError, ToolError, ErrorType

__all__ = [
    # Conversation
    "ConversationState",
    "ConversationContext",
    "Message",
    "MessageRole",
    # Customer
    "CustomerContext",
    # Intent
    "Intent",
    "IntentType",
    # NLP
    "ExtractedInformation",
    "MissingInformation",
    "NLPResult",
    # Reservation
    "ReservationRequest",
    "ReservationData",
    "ReservationConfirmation",
    "ReservationStatus",
    # Availability
    "AvailabilityRequest",
    "AvailabilityResult",
    "TableOption",
    "TableStatus",
    # Recommendation
    "RecommendationRequest",
    "RecommendationResult",
    "RecommendedItem",
    # Payment
    "PaymentRequest",
    "PaymentResult",
    "PaymentStatus",
    # Notification
    "NotificationRequest",
    "NotificationResult",
    # Handoff
    "HumanHandoffRequest",
    "HumanHandoffResult",
    # Errors
    "AgentError",
    "ToolError",
    "ErrorType",
]