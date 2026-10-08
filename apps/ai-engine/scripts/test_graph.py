#!/usr/bin/env python
"""Script pour tester le graphe LangGraph."""

import sys
import uuid
from datetime import datetime

# Ajouter le chemin du projet
sys.path.insert(0, ".")

from app.graph import (
    create_initial_state,
    get_graph,
    add_user_message,
    add_assistant_message,
)
from app.schemas.customer import CustomerContext


def test_graph_simple():
    """Teste le graphe avec une demande simple."""
    print("=" * 60)
    print("🔍 TEST DU GRAPHE LANGGRAPH")
    print("=" * 60)
    
    # Créer un client
    customer = CustomerContext(
        name="Jean Dupont",
        phone="+243123456789",
        preferred_language="fr"
    )
    
    # Créer un état initial
    state = create_initial_state(
        conversation_id=f"test-{uuid.uuid4().hex[:8]}",
        restaurant_id="rest-test-001",
        channel="chat",
        customer=customer,
        max_iterations=5,
    )
    
    # Ajouter un message utilisateur
    add_user_message(
        state, 
        "Bonjour, je voudrais réserver une table pour demain soir à 20h pour 4 personnes."
    )
    
    print("\n📌 État initial:")
    print(f"  Conversation: {state['conversation_id']}")
    print(f"  Restaurant: {state['restaurant_id']}")
    print(f"  Client: {state.get('customer')}")
    print(f"  Messages: {len(state['messages'])}")
    print(f"  Dernier message: {state['messages'][-1].content}")
    
    # Récupérer le graphe
    print("\n🚀 Récupération du graphe...")
    try:
        graph = get_graph()
        print("  ✅ Graphe récupéré")
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        return False
    
    # Exécuter le graphe
    print("\n🚀 Exécution du graphe...")
    config = {"configurable": {"thread_id": state["conversation_id"]}}
    
    try:
        result = graph.invoke(state, config)
        
        print("\n📌 Résultat:")
        print(f"  Intention: {result.get('intent')}")
        print(f"  Agent actuel: {result.get('current_agent')}")
        print(f"  Itération: {result.get('iteration')}")
        print(f"  Réservation: {result.get('reservation')}")
        
        print("\n✅ Test réussi !")
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur lors de l'exécution: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_graph_handoff():
    """Teste le graphe avec une demande de transfert humain."""
    print("\n" + "=" * 60)
    print("🔍 TEST DU TRANSFERT HUMAIN")
    print("=" * 60)
    
    # Créer un client
    customer = CustomerContext(
        name="Marie Claire",
        phone="+243987654321",
        preferred_language="fr"
    )
    
    # Créer un état initial
    state = create_initial_state(
        conversation_id=f"test-handoff-{uuid.uuid4().hex[:8]}",
        restaurant_id="rest-test-001",
        channel="chat",
        customer=customer,
        max_iterations=5,
    )
    
    # Ajouter un message utilisateur
    add_user_message(state, "Je veux parler à un humain")
    
    print("\n📌 État initial:")
    print(f"  Conversation: {state['conversation_id']}")
    print(f"  Dernier message: {state['messages'][-1].content}")
    
    # Récupérer le graphe
    graph = get_graph()
    
    # Exécuter le graphe
    print("\n🚀 Exécution du graphe...")
    config = {"configurable": {"thread_id": state["conversation_id"]}}
    
    try:
        result = graph.invoke(state, config)
        
        print("\n📌 Résultat:")
        print(f"  Intention: {result.get('intent')}")
        print(f"  Transfert humain: {result.get('handoff')}")
        
        if result.get('handoff') and result['handoff'].required:
            print("  ✅ Transfert humain déclenché")
        else:
            print("  ❌ Transfert humain non déclenché")
        
        return result.get('handoff') and result['handoff'].required
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Exécute tous les tests."""
    success = True
    
    print("\n" + "=" * 60)
    print("🧪 DÉMARRAGE DES TESTS")
    print("=" * 60)
    
    # Test 1
    if not test_graph_simple():
        success = False
    
    # Test 2
    if not test_graph_handoff():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Tous les tests du graphe sont passés !")
    else:
        print("❌ Certains tests ont échoué.")
        print("\nVérifiez:")
        print("  1. Que toutes les dépendances sont installées")
        print("  2. Que les imports sont corrects")
        print("  3. La version de LangGraph")
    print("=" * 60)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())