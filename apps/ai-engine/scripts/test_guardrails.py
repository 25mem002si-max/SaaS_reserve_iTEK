#!/usr/bin/env python
"""Script pour tester les Guardrails."""

import sys
sys.path.insert(0, ".")

print("=" * 60, flush=True)
print("🔍 TEST DES GUARDRAILS", flush=True)
print("=" * 60, flush=True)

try:
    from app.guardrails.validation import DataValidator, ResponseGuard
    from app.guardrails.hallucination import get_hallucination_guard
    from app.guardrails.safety import get_safety_guard, get_pii_guard
    
    print("\n📌 Test 1: Validation des données", flush=True)
    validator = DataValidator()
    
    # Tester avec des données invalides
    result = validator.validate_reservation_data(
        type('obj', (object,), {
            'date': None,
            'time': "25:00",
            'guests_count': 0,
            'currency': "EUR",
        })()
    )
    print(f"  Validation: valide={result['valid']}", flush=True)
    print(f"  Erreurs: {result['errors']}", flush=True)
    
    print("\n📌 Test 2: Anti-hallucination", flush=True)
    guard = get_hallucination_guard()
    
    # Réponse avec hallucination
    context = {
        "has_verified_availability": False,
        "has_verified_prices": False,
        "reservation_created": False,
    }
    response = "Votre table est disponible et coûte 50 USD. Réservation confirmée !"
    
    result = guard.validate_agent_response("test", response, context)
    print(f"  Valide: {result['valid']}", flush=True)
    print(f"  Problèmes: {result['issues']}", flush=True)
    
    print("\n📌 Test 3: Sécurité", flush=True)
    safety = get_safety_guard()
    pii = get_pii_guard()
    
    # Tester la validation de téléphone
    phone = "+243123456789"
    print(f"  Téléphone valide: {safety.validate_phone_number(phone)}", flush=True)
    print(f"  Téléphone masqué: {pii.mask_phone_number(phone)}", flush=True)
    
    # Tester l'email
    email = "test@example.com"
    print(f"  Email valide: {safety.validate_email(email)}", flush=True)
    print(f"  Email masqué: {pii.mask_email(email)}", flush=True)
    
    print("\n" + "=" * 60, flush=True)
    print("✅ Tests terminés", flush=True)
    print("=" * 60, flush=True)

except Exception as e:
    print(f"\n❌ Erreur: {e}", flush=True)
    import traceback
    traceback.print_exc()