#!/usr/bin/env python
"""Script pour tester l'Agent Réservation."""

import sys
import uuid
from datetime import datetime, timedelta

sys.path.insert(0, ".")

from app.agents.reservation_agent import get_reservation_agent
from app.schemas.reservation import ReservationData
from app.graph import create_initial_state, add_user_message
from app.schemas.customer import CustomerContext


def test_reservation():
    """Teste l'Agent Réservation."""
    print("=" * 60)
    print("🔍 TEST DE L'AGENT RÉSERVATION")
    print("=" * 60)
    
    agent = get_reservation_agent()
    
    # Créer un client
    customer = CustomerContext(
        name="Jean Dupont",
        phone="+243123456789",
        preferred_language="fr"
    )
    
    # Créer un état
    state = create_initial_state(
        conversation_id=f"test-{uuid.uuid4().hex[:8]}",
        restaurant_id="rest-test-001",
        channel="chat",
        customer=customer,
    )
    
    # Ajouter des messages
    add_user_message(state, "Bonjour, je voudrais réserver une table pour demain soir à 20h pour 4 personnes.")
    
    # Créer les données de réservation
    reservation = ReservationData(
        date=datetime.now() + timedelta(days=1),
        time="20:00",
        guests_count=4,
        preferences=["poisson"],
        customer_name="Jean Dupont",
        customer_phone="+243123456789",
    )
    state["reservation"] = reservation
    
    print("\n📌 Données de réservation:")
    print(f"  - Date: {reservation.date}")
    print(f"  - Heure: {reservation.time}")
    print(f"  - Couverts: {reservation.guests_count}")
    print(f"  - Préférences: {reservation.preferences}")
    
    print("\n🚀 Exécution du processus de réservation...")
    
    try:
        result = agent.process_reservation(state)
        
        print("\n📌 Résultat:")
        print(f"  - Prochaine action: {result.get('next_action')}")
        print(f"  - Table sélectionnée: {result.get('selected_table')}")
        
        confirmation = result.get('reservation_confirmation')
        if confirmation:
            print(f"  - Réservation ID: {confirmation.reservation_id}")
            print(f"  - Statut: {confirmation.status.value}")
            print(f"  - Message: {confirmation.message}")
        
        print(f"  - Paiement requis: {result.get('payment_required', False)}")
        
        print("\n✅ Test réussi !")
        return True
        
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    success = test_reservation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()