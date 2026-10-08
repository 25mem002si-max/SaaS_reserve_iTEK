"""Définition des nœuds du graphe LangGraph."""

from typing import Dict, Any
import logging
import re
from datetime import datetime

# IMPORT MANQUANT - Ajoutez cette ligne
from app.graph.state import (
    ConversationState,
    should_handoff,      # <--- AJOUTÉ
    get_handoff_summary, # <--- AJOUTÉ
)
from app.schemas.intent import Intent, IntentType
from app.schemas.reservation import ReservationData, ReservationStatus
from app.schemas.handoff import HumanHandoffResult, HandoffReason

logger = logging.getLogger("ai_engine.graph.nodes")


def load_context_node(state: ConversationState) -> Dict[str, Any]:
    """Charge le contexte de la conversation."""
    logger.info(f"📂 LOAD_CONTEXT - {state.get('conversation_id')}")
    
    messages = state.get("messages", [])
    last_message = messages[-1] if messages else None
    
    return {
        "metadata": {
            "is_new_conversation": len(messages) <= 1,
            "last_message": last_message.content if last_message else None,
            "message_count": len(messages),
        },
        "iteration": state.get("iteration", 0) + 1,
        "current_agent": "orchestrator",
        "error": None,
        "error_count": 0,
    }


def orchestrator_node(state: ConversationState) -> Dict[str, Any]:
    """Nœud Orchestrateur."""
    logger.info(f"🎯 ORCHESTRATOR - {state.get('conversation_id')}")

    reservation = state.get("reservation")
    payment = state.get("payment")
    last_message = state.get("messages", [])[-1].content if state.get("messages") else ""
    has_phone_number = bool(re.search(r"(?<!\d)\+?[0-9][0-9\s-]{7,14}(?!\d)", last_message))
    if reservation and has_phone_number:
        return {
            "next_action": "payment" if payment and payment.is_pending() else "reservation",
            "current_agent": "orchestrator",
            "requires_clarification": False,
            "clarification_question": None,
            "message": "Merci, j'ai bien enregistré votre numéro. Je poursuis la vérification du paiement en cours." if payment and payment.is_pending() else None,
        }

    if should_handoff(state):
        logger.info("  → Transfert humain")
        return {"next_action": "human_handoff", "current_agent": "orchestrator"}
    
    from app.agents.orchestrator import analyze_intent
    
    try:
        intent = analyze_intent(state)
        logger.info(f"  → Intention: {intent.type.value} ({intent.confidence:.2f})")
        
        # Supprimer self._get_next_action - utiliser une fonction locale
        if intent.type == IntentType.NEW_RESERVATION:
            next_action = "nlp_extraction"
        elif intent.type == IntentType.CHECK_AVAILABILITY:
            next_action = "reservation"
        elif intent.type == IntentType.GET_RECOMMENDATIONS:
            next_action = "recommendation"
        elif intent.type == IntentType.PAYMENT:
            next_action = "payment"
        elif intent.type in {IntentType.MODIFY_RESERVATION, IntentType.CANCEL_RESERVATION}:
            next_action = "reservation"
        elif intent.type == IntentType.HUMAN_HANDOFF:
            next_action = "human_handoff"
        elif intent.type == IntentType.GREETING:
            next_action = "greeting_response"
        else:
            next_action = "unknown_response"
        
        if intent.requires_clarification and intent.clarification_question and intent.type != IntentType.NEW_RESERVATION:
            next_action = "ask_missing_info"
        
        return {
            "intent": intent,
            "current_agent": "orchestrator",
            "next_action": next_action,
            "requires_clarification": intent.requires_clarification,
            "clarification_question": intent.clarification_question,
        }
    except Exception as e:
        logger.error(f"Erreur orchestrator: {e}")
        return {
            "error": str(e),
            "error_count": state.get("error_count", 0) + 1,
            "current_agent": "orchestrator",
            "next_action": "error",
        }


def nlp_agent_node(state: ConversationState) -> Dict[str, Any]:
    """Nœud NLP."""
    logger.info(f"🧠 NLP_AGENT - {state.get('conversation_id')}")
    
    messages = state.get("messages", [])
    user_messages = [m for m in messages if m.role == "user"]
    
    if not user_messages:
        return {"error": "Aucun message", "current_agent": "nlp_agent", "next_action": "error"}
    
    from app.agents.nlp_agent import process_message
    
    try:
        conversation_context = "\n".join(
            f"{message.role.value}: {message.content}"
            for message in messages[-6:]
        )
        result = process_message(
            user_messages[-1].content,
            conversation_id=state.get("conversation_id", "unknown"),
            conversation_context=conversation_context,
        )
        extracted = result.extracted

        previous = state.get("extracted_info")
        if previous:
            from app.agents.nlp_agent import get_nlp_agent
            extracted = get_nlp_agent()._merge_extractions(previous, extracted)
            result = get_nlp_agent().get_nlp_result(extracted)

        reservation = state.get("reservation")
        if result.is_complete and reservation is None:
            customer = state.get("customer")
            return {
                "extracted_info": extracted,
                "nlp_result": result,
                "reservation": ReservationData(
                    date=extracted.date,
                    time=extracted.time,
                    guests_count=extracted.guests_count,
                    preferences=extracted.preferences,
                    allergies=extracted.allergies,
                    budget=extracted.budget,
                    currency=extracted.currency or "USD",
                    customer_name=customer.name if customer else None,
                    customer_phone=customer.phone if customer else None,
                ),
                "current_agent": "nlp_agent",
                "next_action": "reservation",
                "requires_clarification": False,
                "clarification_question": None,
            }
        
        return {
            "extracted_info": extracted,
            "nlp_result": result,
            "current_agent": "nlp_agent",
            "next_action": "reservation" if result.is_complete else "ask_missing_info",
            "requires_clarification": not result.is_complete,
            "clarification_question": result.next_question,
        }
    except Exception as e:
        return {
            "error": str(e),
            "error_count": state.get("error_count", 0) + 1,
            "current_agent": "nlp_agent",
            "next_action": "error",
        }


def reservation_agent_node(state: ConversationState) -> Dict[str, Any]:
    """Nœud Réservation - Gère la logique de réservation."""
    logger.info(f"📅 RESERVATION_AGENT - {state.get('conversation_id')}")
    
    from app.agents.reservation_agent import process_reservation
    
    try:
        result = process_reservation(state)
        return {
            **result,
            "current_agent": "reservation_agent",
        }
    except Exception as e:
        logger.error(f"Erreur reservation: {e}")
        return {
            "error": str(e),
            "error_count": state.get("error_count", 0) + 1,
            "current_agent": "reservation_agent",
            "next_action": "error",
        } 


def recommendation_agent_node(state: ConversationState) -> Dict[str, Any]:
    """Nœud Recommandation - Recommande des plats selon les préférences."""
    logger.info(f"🍽️ RECOMMENDATION_AGENT - {state.get('conversation_id')}")
    
    from app.agents.recommendation_agent import process_recommendation
    
    try:
        result = process_recommendation(state)
        return {
            **result,
            "current_agent": "recommendation_agent",
        }
    except Exception as e:
        logger.error(f"Erreur recommendation: {e}")
        return {
            "error": str(e),
            "error_count": state.get("error_count", 0) + 1,
            "current_agent": "recommendation_agent",
            "next_action": "error",
        }


def payment_agent_node(state: ConversationState) -> Dict[str, Any]:
    """Nœud Paiement - Gère la logique de paiement."""
    logger.info(f"💰 PAYMENT_AGENT - {state.get('conversation_id')}")
    
    from app.agents.payment_agent import process_payment
    
    try:
        result = process_payment(state)
        return {
            **result,
            "current_agent": "payment_agent",
        }
    except Exception as e:
        logger.error(f"Erreur paiement: {e}")
        return {
            "error": str(e),
            "error_count": state.get("error_count", 0) + 1,
            "current_agent": "payment_agent",
            "next_action": "error",
        }


def notification_agent_node(state: ConversationState) -> Dict[str, Any]:
    """Nœud Notification - Envoie les notifications et reçus."""
    logger.info(f"📨 NOTIFICATION_AGENT - {state.get('conversation_id')}")
    
    from app.agents.notification_agent import process_notification
    
    try:
        result = process_notification(state)
        return {
            **result,
            "current_agent": "notification_agent",
        }
    except Exception as e:
        logger.error(f"Erreur notification: {e}")
        return {
            "error": str(e),
            "error_count": state.get("error_count", 0) + 1,
            "current_agent": "notification_agent",
            "next_action": "error",
        }

def human_handoff_node(state: ConversationState) -> Dict[str, Any]:
    """Nœud Transfert Humain."""
    logger.info(f"👤 HUMAN_HANDOFF - {state.get('conversation_id')}")
    
    handoff = HumanHandoffResult.create_handoff(
        reason=state.get("handoff_reason") or HandoffReason.REQUESTED_BY_USER,
        message="Je vous transfère à l'équipe.",
        summary=get_handoff_summary(state),
    )
    
    return {
        "handoff": handoff,
        "current_agent": "human_handoff",
        "next_action": "end",
        "is_complete": True,
    }