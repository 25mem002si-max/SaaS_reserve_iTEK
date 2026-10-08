#!/usr/bin/env python
"""Script pour tester l'Agent Paiement."""

import sys
import uuid
from datetime import datetime, timedelta

sys.path.insert(0, ".")

print("=" * 60, flush=True)
print("🔍 TEST DE L'AGENT PAIEMENT", flush=True)
print("=" * 60, flush=True)

try:
    from app.agents.payment_agent import get_payment_agent
    from app.schemas.customer import CustomerContext
    from app.schemas.reservation import ReservationData
    
    print("\n📌 Création de l'agent...", flush=True)
    agent = get_payment_agent()
    print("  ✅ Agent créé", flush=True)
    
    # Créer un client
    customer = CustomerContext(
        name="Jean Dupont",
        phone="+243123456789",
        preferred_language="fr"
    )
    
    # Créer une réservation
    reservation = ReservationData(
        date=datetime.now() + timedelta(days=1),
        time="20:00",
        guests_count=4,
        preferences=["poisson"],
        deposit_required=True,
        deposit_amount=10.0,
        currency="USD",
        customer_name="Jean Dupont",
        customer_phone="+243123456789",
    )
    
    # Créer un état
    state = {
        "conversation_id": f"test-{uuid.uuid4().hex[:8]}",
        "restaurant_id": "rest-test-001",
        "channel": "chat",
        "customer": customer,
        "reservation": reservation,
        "reservation_confirmation": {
            "reservation_id": "res-test-001",
        },
    }
    
    print("\n📌 Données de paiement:")
    print(f"  - Client: {customer.name}")
    print(f"  - Téléphone: {customer.phone}")
    print(f"  - Montant: {reservation.deposit_amount} {reservation.currency}")
    print(f"  - Réservation: {reservation.guests_count} personnes")
    
    print("\n🚀 Exécution du processus de paiement...", flush=True)
    result = agent.process_payment(state)
    
    print("\n📌 Résultat:", flush=True)
    print(f"  - Prochaine action: {result.get('next_action')}", flush=True)
    print(f"  - Message: {result.get('message')}", flush=True)
    
    payment = result.get('payment')
    if payment:
        print(f"  - Paiement ID: {payment.payment_id}", flush=True)
        print(f"  - Statut: {payment.status.value}", flush=True)
        print(f"  - Montant: {payment.amount} {payment.currency}", flush=True)
    
    print("\n" + "=" * 60, flush=True)
    print("✅ Test terminé", flush=True)
    print("=" * 60, flush=True)

except Exception as e:
    print(f"\n❌ Erreur: {e}", flush=True)
    import traceback
    traceback.print_exc()