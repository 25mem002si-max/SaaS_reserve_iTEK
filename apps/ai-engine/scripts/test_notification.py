#!/usr/bin/env python
"""Script pour tester l'Agent Notification."""

import sys
import uuid
from datetime import datetime, timedelta

sys.path.insert(0, ".")

print("=" * 60, flush=True)
print("🔍 TEST DE L'AGENT NOTIFICATION", flush=True)
print("=" * 60, flush=True)

try:
    from app.agents.notification_agent import get_notification_agent
    from app.schemas.customer import CustomerContext
    from app.schemas.reservation import ReservationConfirmation, ReservationStatus
    
    print("\n📌 Création de l'agent...", flush=True)
    agent = get_notification_agent()
    print("  ✅ Agent créé", flush=True)
    
    # Créer un client
    customer = CustomerContext(
        name="Jean Dupont",
        phone="+243123456789",
        preferred_language="fr"
    )
    
    # Créer une confirmation
    confirmation = ReservationConfirmation(
        reservation_id="res-test-001",
        table_id="table-001",
        table_label="Table 4",
        customer_name="Jean Dupont",
        date=datetime.now() + timedelta(days=1),
        guests_count=4,
        status=ReservationStatus.CONFIRMED,
        deposit_paid=False,
        deposit_amount=10.0,
        currency="USD",
        message="Réservation confirmée",
    )
    
    # Créer un état
    state = {
        "conversation_id": f"test-{uuid.uuid4().hex[:8]}",
        "restaurant_id": "rest-test-001",
        "channel": "chat",
        "customer": customer,
        "reservation_confirmation": confirmation,
    }
    
    print("\n📌 Données de notification:")
    print(f"  - Client: {customer.name}")
    print(f"  - Téléphone: {customer.phone}")
    print(f"  - Réservation ID: {confirmation.reservation_id}")
    print(f"  - Table: {confirmation.table_label}")
    print(f"  - Date: {confirmation.date}")
    
    print("\n🚀 Exécution du processus de notification...", flush=True)
    result = agent.process_notification(state)
    
    print("\n📌 Résultat:", flush=True)
    print(f"  - Notification envoyée: {result.get('notification_sent')}", flush=True)
    print(f"  - Rappel planifié: {result.get('reminder_scheduled')}", flush=True)
    print(f"  - Message: {result.get('message')}", flush=True)
    
    receipt = result.get('receipt')
    if receipt:
        print(f"  - PDF URL: {receipt.get('pdf_url')}", flush=True)
        print(f"  - QR Code Token: {receipt.get('qr_code_token')}", flush=True)
    
    print("\n" + "=" * 60, flush=True)
    print("✅ Test terminé", flush=True)
    print("=" * 60, flush=True)

except Exception as e:
    print(f"\n❌ Erreur: {e}", flush=True)
    import traceback
    traceback.print_exc()