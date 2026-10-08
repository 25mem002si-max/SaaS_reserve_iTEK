#!/usr/bin/env python
"""Script pour tester l'Agent Orchestrateur."""

import sys
import uuid
from datetime import datetime

sys.path.insert(0, ".")

from app.agents.orchestrator import get_orchestrator_agent
from app.graph import create_initial_state, add_user_message
from app.schemas.customer import CustomerContext


def test_orchestrator():
    """Teste l'Agent Orchestrateur avec différents messages."""
    print("=" * 60)
    print("🔍 TEST DE L'AGENT ORCHESTRATEUR")
    print("=" * 60)
    
    orchestrator = get_orchestrator_agent()
    
    test_cases = [
        {
            "name": "Réservation complète",
            "message": "Bonjour, je voudrais réserver une table pour demain soir à 20h pour 4 personnes."
        },
        {
            "name": "Réservation avec peu d'infos",
            "message": "Je voudrais réserver une table."
        },
        {
            "name": "Vérification disponibilité",
            "message": "Est-ce que vous avez une table libre ce soir ?"
        },
        {
            "name": "Recommandation",
            "message": "Qu'est-ce que vous me recommandez comme plat ?"
        },
        {
            "name": "Paiement",
            "message": "Je veux payer l'acompte pour ma réservation."
        },
        {
            "name": "Transfert humain",
            "message": "Je veux parler à un humain."
        },
        {
            "name": "Salutation",
            "message": "Bonjour !"
        },
        {
            "name": "Message inconnu",
            "message": "Blablabla, je ne sais pas quoi dire."
        },
    ]
    
    success_count = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n📌 Test {i}: {test['name']}")
        print(f"   Message: {test['message']}")
        
        try:
            # Créer un état
            state = create_initial_state(
                conversation_id=f"test-{uuid.uuid4().hex[:8]}",
                restaurant_id="rest-test-001",
                channel="chat",
            )
            add_user_message(state, test['message'])
            
            # Analyser
            intent = orchestrator.analyze(state)
            
            print(f"   Résultat:")
            print(f"     - Intention: {intent.type.value}")
            print(f"     - Confiance: {intent.confidence:.2f}")
            print(f"     - Clarification: {intent.requires_clarification}")
            if intent.clarification_question:
                print(f"     - Question: {intent.clarification_question}")
            if intent.alternative_intents:
                print(f"     - Alternatives: {[i.value for i in intent.alternative_intents]}")
            
            success_count += 1
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"✅ {success_count}/{len(test_cases)} tests passés")
    print("=" * 60)
    
    return success_count == len(test_cases)


def test_orchestrator_with_context():
    """Teste l'Orchestrator avec un contexte de réservation existant."""
    print("\n" + "=" * 60)
    print("🔍 TEST AVEC CONTEXTE EXISTANT")
    print("=" * 60)
    
    orchestrator = get_orchestrator_agent()
    
    # Créer un état avec une réservation en cours
    customer = CustomerContext(
        name="Jean Dupont",
        phone="+243123456789",
        preferred_language="fr"
    )
    
    state = create_initial_state(
        conversation_id=f"test-{uuid.uuid4().hex[:8]}",
        restaurant_id="rest-test-001",
        channel="chat",
        customer=customer,
    )
    
    # Ajouter quelques messages
    add_user_message(state, "Bonjour, je voudrais réserver une table pour demain.")
    add_user_message(state, "Pour 4 personnes.")
    add_user_message(state, "Je voudrais changer la date pour après-demain.")
    
    # Analyser
    print(f"\n📌 Contexte:")
    print(f"   Client: {customer.name}")
    print(f"   Messages: {len(state.get('messages', []))}")
    print(f"   Dernier message: {state.get('messages', [])[-1].content}")
    
    intent = orchestrator.analyze(state)
    
    print(f"\n📌 Résultat:")
    print(f"   - Intention: {intent.type.value}")
    print(f"   - Confiance: {intent.confidence:.2f}")
    
    return True


if __name__ == "__main__":
    success = test_orchestrator()
    if success:
        test_orchestrator_with_context()
    sys.exit(0 if success else 1)