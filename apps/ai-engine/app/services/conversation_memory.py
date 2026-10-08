"""Mémoire de conversation persistante pour les agents."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.config.settings import settings

logger = logging.getLogger("ai_engine.services.conversation_memory")

_STATE_FIELDS = {
    "conversation_id",
    "restaurant_id",
    "channel",
    "messages",
    "customer",
    "intent",
    "extracted_info",
    "nlp_result",
    "reservation",
    "reservation_confirmation",
    "availability",
    "selected_table",
    "recommendation",
    "payment",
    "payment_required",
    "handoff",
    "handoff_reason",
    "current_agent",
    "next_action",
    "iteration",
    "max_iterations",
    "error",
    "error_count",
    "retry_count",
    "metadata",
    "conversation_summary",
    "requires_clarification",
    "clarification_question",
    "message",
    "is_complete",
    "waiting_for_payment",
    "lock_token",
}

try:
    import redis
except ImportError:  # pragma: no cover - dépendance optionnelle pour tests
    redis = None


class ConversationMemoryService:
    """Stockage léger de l'historique de conversation.

    Le service utilise Redis quand il est disponible et retombe sur un stockage
    mémoire local pour rester fonctionnel sans service externe.
    """

    def __init__(self, redis_client: Any | None = None):
        self.redis_client = redis_client
        if self.redis_client is None and redis is not None:
            try:
                self.redis_client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
                self.redis_client.ping()
            except Exception as exc:  # pragma: no cover - dépend du runtime
                logger.warning("Redis indisponible pour la mémoire de conversation: %s", exc)
                self.redis_client = None
        self._fallback_store: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def _key(conversation_id: str) -> str:
        return f"ai_engine:conversation:{conversation_id}"

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _normalize_message(message: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(message, BaseModel):
            message = message.model_dump(mode="json")
        role = message.get("role")
        return {
            "role": str(role or "user"),
            "content": str(message.get("content") or ""),
            "timestamp": message.get("timestamp") or ConversationMemoryService._now_iso(),
            "agent_name": message.get("agent_name"),
            "metadata": message.get("metadata") or {},
        }

    @staticmethod
    def _build_summary(messages: List[Dict[str, Any]], state: Optional[Dict[str, Any]] = None) -> str:
        if not messages:
            return "Aucune conversation antérieure."

        state = state or {}
        reservation = state.get("reservation") or {}
        extracted = state.get("extracted_info") or {}
        customer = state.get("customer") or {}

        def value(record: Any, field: str) -> Any:
            return record.get(field) if isinstance(record, dict) else getattr(record, field, None)

        guest_count = value(reservation, "guests_count") or value(extracted, "guests_count")
        date = value(reservation, "date") or value(extracted, "date")
        time = value(reservation, "time") or value(extracted, "time")
        customer_name = value(customer, "name") or value(reservation, "customer_name")
        phone = value(customer, "phone") or value(reservation, "customer_phone")
        if guest_count or date or time or customer_name or phone or reservation:
            parts = []
            if customer_name:
                parts.append(f"client: {customer_name}")
            if reservation:
                parts.append("réservation en cours")
            elif guest_count or date or time:
                parts.append("demande de réservation en cours")
            if date:
                if isinstance(date, str):
                    try:
                        date = datetime.fromisoformat(date)
                    except ValueError:
                        pass
                parts.append(f"date: {date.strftime('%d/%m/%Y') if hasattr(date, 'strftime') else date}")
            if time:
                parts.append(f"heure: {time}")
            if guest_count:
                parts.append(f"{guest_count} personnes")
            if phone:
                parts.append("téléphone fourni")
            if state.get("next_action"):
                parts.append(f"étape: {state['next_action']}")
            return "; ".join(parts)

        normalized = [ConversationMemoryService._normalize_message(message) for message in messages]
        text = " ".join(message["content"] for message in normalized).lower()

        summary_parts: List[str] = []
        if any(keyword in text for keyword in ["réserver", "reservation", "table", "couverts", "personnes"]):
            summary_parts.append("demande de réservation")
            summary_parts.append("réserver")
        if any(keyword in text for keyword in ["payer", "paiement", "payé", "payement"]):
            summary_parts.append("paiement")
        if any(keyword in text for keyword in ["recommand", "conseil", "suggest", "plat", "menu"]):
            summary_parts.append("recommandation")
        if any(keyword in text for keyword in ["annuler", "supprimer", "annulation"]):
            summary_parts.append("annulation")

        if "demain" in text:
            summary_parts.append("date: demain")
        if "aujourd'hui" in text or "ce soir" in text:
            summary_parts.append("date: aujourd'hui / ce soir")

        if "personne" in text or "personnes" in text:
            summary_parts.append("nombre de personnes mentionné")
        if "téléphone" in text or "+243" in text or "097" in text or "phone" in text:
            summary_parts.append("numéro de téléphone fourni")

        if not summary_parts:
            summary_parts.append("conversation active")

        return "; ".join(summary_parts[:5])

    def load_context(self, conversation_id: str) -> Dict[str, Any]:
        key = self._key(conversation_id)

        if self.redis_client is not None:
            try:
                raw = self.redis_client.get(key)
                if raw:
                    payload = json.loads(raw)
                    payload["messages"] = [self._normalize_message(message) for message in payload.get("messages", [])]
                    payload["summary"] = payload.get("summary") or self._build_summary(
                        payload["messages"], payload.get("state")
                    )
                    return payload
            except Exception as exc:  # pragma: no cover - dépend du runtime
                logger.warning("Erreur lecture Redis mémoire: %s", exc)

        payload = self._fallback_store.get(conversation_id)
        if payload:
            payload = dict(payload)
            payload["messages"] = [self._normalize_message(message) for message in payload.get("messages", [])]
            payload["summary"] = payload.get("summary") or self._build_summary(
                payload["messages"], payload.get("state")
            )
            return payload

        return {"messages": [], "summary": "Aucune conversation antérieure.", "updated_at": self._now_iso()}

    @staticmethod
    def _to_json_value(value: Any) -> Any:
        if isinstance(value, BaseModel):
            return value.model_dump(mode="json")
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, dict):
            return {key: ConversationMemoryService._to_json_value(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [ConversationMemoryService._to_json_value(item) for item in value]
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    @classmethod
    def serialize_state(cls, state: Dict[str, Any]) -> Dict[str, Any]:
        return {
            key: cls._to_json_value(value)
            for key, value in state.items()
            if key in _STATE_FIELDS
        }

    @staticmethod
    def restore_state(context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        saved_state = context.get("state")
        if not isinstance(saved_state, dict):
            return None

        from app.graph.state import ConversationState
        from app.schemas.availability import AvailabilityResult, TableOption
        from app.schemas.conversation import Message
        from app.schemas.customer import CustomerContext
        from app.schemas.errors import AgentError
        from app.schemas.handoff import HandoffReason, HumanHandoffResult
        from app.schemas.intent import Intent
        from app.schemas.nlp import ExtractedInformation, NLPResult
        from app.schemas.payment import PaymentResult
        from app.schemas.recommendation import RecommendationResult
        from app.schemas.reservation import ReservationConfirmation, ReservationData

        model_fields = {
            "customer": CustomerContext,
            "intent": Intent,
            "extracted_info": ExtractedInformation,
            "nlp_result": NLPResult,
            "reservation": ReservationData,
            "reservation_confirmation": ReservationConfirmation,
            "availability": AvailabilityResult,
            "selected_table": TableOption,
            "recommendation": RecommendationResult,
            "payment": PaymentResult,
            "handoff": HumanHandoffResult,
            "error": AgentError,
        }
        restored: ConversationState = dict(saved_state)
        restored["messages"] = [Message.model_validate(message) for message in saved_state.get("messages", [])]
        for field, model in model_fields.items():
            value = saved_state.get(field)
            if value is not None and not isinstance(value, model):
                try:
                    restored[field] = model.model_validate(value)
                except (TypeError, ValueError):
                    if field == "error":
                        restored.pop(field, None)
                    else:
                        raise
        if restored.get("handoff_reason") is not None and not isinstance(restored["handoff_reason"], HandoffReason):
            restored["handoff_reason"] = HandoffReason(restored["handoff_reason"])
        return restored

    def save_turn(
        self,
        conversation_id: str,
        user_message: Optional[str] = None,
        assistant_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload = self.load_context(conversation_id)
        serialized_state = self.serialize_state(state) if state is not None else None
        messages: List[Dict[str, Any]] = (
            [self._normalize_message(message) for message in serialized_state.get("messages", [])]
            if serialized_state is not None
            else list(payload.get("messages", []))
        )

        if serialized_state is None and user_message is not None:
            messages.append({
                "role": "user",
                "content": str(user_message),
                "timestamp": self._now_iso(),
                "agent_name": None,
                "metadata": metadata or {},
            })

        if serialized_state is None and assistant_message is not None:
            messages.append({
                "role": "assistant",
                "content": str(assistant_message),
                "timestamp": self._now_iso(),
                "agent_name": "assistant",
                "metadata": metadata or {},
            })

        messages = messages[-30:]
        if serialized_state is not None:
            serialized_state["messages"] = messages
        summary = self._build_summary(messages, serialized_state)
        if serialized_state is not None:
            serialized_state["conversation_summary"] = summary
        saved = {
            "messages": messages,
            "summary": summary,
            "updated_at": self._now_iso(),
            "metadata": metadata or {},
            "state": serialized_state,
        }

        if self.redis_client is not None:
            try:
                self.redis_client.set(
                    self._key(conversation_id),
                    json.dumps(saved, ensure_ascii=False),
                    ex=settings.redis_session_ttl_seconds or 3600,
                )
            except Exception as exc:  # pragma: no cover - dépend du runtime
                logger.warning("Erreur écriture Redis mémoire: %s", exc)
                self._fallback_store[conversation_id] = saved
        else:
            self._fallback_store[conversation_id] = saved

        return saved


_conversation_memory_service: Optional[ConversationMemoryService] = None


def get_conversation_memory_service() -> ConversationMemoryService:
    global _conversation_memory_service
    if _conversation_memory_service is None:
        _conversation_memory_service = ConversationMemoryService()
    return _conversation_memory_service
