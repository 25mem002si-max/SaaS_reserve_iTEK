"""Fonctions de routage pour le graphe LangGraph."""

from typing import Literal

from app.graph.state import ConversationState, should_handoff


def route_orchestrator(state: ConversationState) -> Literal[
    "nlp_extraction",
    "reservation",
    "recommendation",
    "payment",
    "human_handoff",
    "greeting_response",
    "unknown_response",
    "end"
]:
    """Route depuis l'orchestrateur vers le prochain nœud."""
    
    # Vérifier si un transfert humain est nécessaire
    if should_handoff(state):
        return "human_handoff"
    
    next_action = state.get("next_action", "unknown_response")
    
    routing_map = {
        "nlp_extraction": "nlp_extraction",
        "reservation": "reservation",
        "recommendation": "recommendation",
        "payment": "payment",
        "human_handoff": "human_handoff",
        "greeting_response": "greeting_response",
        "unknown_response": "unknown_response",
        "end": "end",
    }
    
    return routing_map.get(next_action, "unknown_response")


def route_nlp(state: ConversationState) -> Literal[
    "reservation",
    "ask_missing_info",
    "recommendation",
    "end"
]:
    """Route depuis le nœud NLP."""
    
    # Vérifier si un transfert humain est nécessaire
    if should_handoff(state):
        return "end"
    
    # Si les informations sont complètes, aller à la réservation
    if state.get("nlp_result") and state["nlp_result"].is_complete:
        return "reservation"
    
    # Sinon, demander les informations manquantes
    return "ask_missing_info"


def route_reservation(state: ConversationState) -> Literal[
    "check_availability",
    "ask_missing_info",
    "payment",
    "confirmation",
    "end"
]:
    """Route depuis le nœud réservation."""
    
    # Vérifier si un transfert humain est nécessaire
    if should_handoff(state):
        return "end"
    
    reservation = state.get("reservation")
    if not reservation:
        return "end"
    
    # Si les informations sont incomplètes
    if not reservation.is_complete():
        return "ask_missing_info"
    
    # Si un paiement est requis
    if state.get("payment_required", False):
        return "payment"
    
    # Si tout est complet, aller à la confirmation
    return "confirmation"


def route_payment(state: ConversationState) -> Literal[
    "confirmation",
    "payment_retry",
    "human_handoff",
    "end"
]:
    """Route depuis le nœud paiement."""
    
    # Vérifier si un transfert humain est nécessaire
    if should_handoff(state):
        return "human_handoff"
    
    payment = state.get("payment")
    if not payment:
        return "payment_retry"
    
    # Si le paiement a réussi
    if payment.is_successful():
        return "confirmation"
    
    # Si le paiement est en attente
    if payment.is_pending():
        return "end"
    
    # Si le paiement a échoué
    return "human_handoff"


def route_after_response(state: ConversationState) -> Literal["end", "continue"]:
    """Route après une réponse."""
    
    # Si la réservation est complète
    if state.get("is_complete", False):
        return "end"
    
    # Si un transfert humain est requis
    if should_handoff(state):
        return "end"
    
    # Sinon, continuer la conversation
    return "continue"


def route_after_error(state: ConversationState) -> Literal["retry", "human_handoff", "end"]:
    """Route après une erreur."""
    
    error_count = state.get("error_count", 0)
    
    # Trop d'erreurs → transfert humain
    if error_count >= 3:
        return "human_handoff"
    
    # Sinon, réessayer
    return "retry"