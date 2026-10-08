"""Construction du graphe LangGraph.

Ce module assemble tous les nœuds et routes
pour former le workflow complet des agents.
"""

from typing import Optional
from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph

# Import de MemorySaver
try:
    from langgraph.checkpoint.memory import MemorySaver
except ImportError:
    try:
        from langgraph.checkpoint import MemorySaver
    except ImportError:
        from langgraph.memory import MemorySaver

import logging

from app.graph.state import ConversationState
from app.graph.nodes import (
    load_context_node,
    orchestrator_node,
    nlp_agent_node,
    reservation_agent_node,
    recommendation_agent_node,
    payment_agent_node,
    notification_agent_node,
    human_handoff_node,
)
from app.graph.routing import (
    route_orchestrator,
    route_nlp,
    route_reservation,
    route_payment,
)

logger = logging.getLogger("ai_engine.graph")


def build_workflow() -> CompiledStateGraph:
    """Construit et compile le graphe LangGraph complet."""
    
    logger.info("🏗️ Construction du graphe LangGraph...")
    
    # Créer le graphe
    workflow = StateGraph(ConversationState)
    
    # === Ajouter les nœuds ===
    # Note: Les noms de nœuds ne doivent pas correspondre aux clés de l'état
    
    # Nœud de chargement du contexte
    workflow.add_node("load_context", load_context_node)
    
    # Nœud orchestrateur
    workflow.add_node("orchestrator", orchestrator_node)
    
    # Nœuds agents - avec des noms uniques qui ne sont pas des clés d'état
    workflow.add_node("nlp_extraction", nlp_agent_node)
    workflow.add_node("reservation_flow", reservation_agent_node)  # Renommé
    workflow.add_node("recommendation_flow", recommendation_agent_node)  # Renommé
    workflow.add_node("payment_flow", payment_agent_node)  # Renommé
    workflow.add_node("confirmation_flow", notification_agent_node)  # Renommé
    workflow.add_node("human_handoff_flow", human_handoff_node)  # Renommé
    
    # Nœuds de réponse (simplifiés)
    workflow.add_node("greeting_response", lambda s: {"current_agent": "greeting", "next_action": "end"})
    workflow.add_node("unknown_response", lambda s: {"current_agent": "unknown", "next_action": "end"})
    workflow.add_node("ask_missing_info", lambda s: {"current_agent": "ask_missing", "next_action": "end"})
    
    # === Ajouter les arêtes ===
    
    # START → load_context
    workflow.set_entry_point("load_context")
    
    # load_context → orchestrator
    workflow.add_edge("load_context", "orchestrator")
    
    # orchestrator → route_orchestrator
    workflow.add_conditional_edges(
        "orchestrator",
        route_orchestrator,
        {
            "nlp_extraction": "nlp_extraction",
            "reservation": "reservation_flow",
            "recommendation": "recommendation_flow",
            "payment": "payment_flow",
            "human_handoff": "human_handoff_flow",
            "greeting_response": "greeting_response",
            "unknown_response": "unknown_response",
            "end": END,
        }
    )
    
    # nlp_extraction → route_nlp
    workflow.add_conditional_edges(
        "nlp_extraction",
        route_nlp,
        {
            "reservation": "reservation_flow",
            "ask_missing_info": "ask_missing_info",
            "recommendation": "recommendation_flow",
            "end": END,
        }
    )
    
    # reservation_flow → route_reservation
    workflow.add_conditional_edges(
        "reservation_flow",
        route_reservation,
        {
            "check_availability": "reservation_flow",
            "ask_missing_info": "ask_missing_info",
            "payment": "payment_flow",
            "confirmation": "confirmation_flow",
            "end": END,
        }
    )
    
    # payment_flow → route_payment
    workflow.add_conditional_edges(
        "payment_flow",
        route_payment,
        {
            "confirmation": "confirmation_flow",
            "payment_retry": "payment_flow",
            "human_handoff": "human_handoff_flow",
            "end": END,
        }
    )
    
    # confirmation_flow → end
    workflow.add_edge("confirmation_flow", END)
    
    # human_handoff_flow → end
    workflow.add_edge("human_handoff_flow", END)
    
    # Nœuds de réponse → end
    workflow.add_edge("greeting_response", END)
    workflow.add_edge("unknown_response", END)
    workflow.add_edge("ask_missing_info", END)
    
    # === Compiler le graphe ===
    
    # Utiliser MemorySaver pour la persistance en mémoire
    memory = MemorySaver()
    
    graph = workflow.compile(checkpointer=memory)
    
    logger.info("✅ Graphe LangGraph compilé avec succès")
    
    return graph


# Instance globale du graphe (singleton)
_graph: Optional[CompiledStateGraph] = None


def get_graph() -> CompiledStateGraph:
    """Retourne l'instance du graphe (singleton)."""
    global _graph
    if _graph is None:
        _graph = build_workflow()
    return _graph


# Pour utilisation directe
graph = get_graph()