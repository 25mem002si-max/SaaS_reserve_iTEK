#!/usr/bin/env python
"""Script pour tester l'Agent NLP (sans LLM)."""

import sys
from datetime import datetime, timedelta

sys.path.insert(0, ".")

from app.agents.nlp_agent import NLPAgent


def test_nlp():
    """Teste l'extraction par patterns uniquement (sans LLM)."""
    print("=" * 60)
    print("🔍 TEST DE L'AGENT NLP (extraction par patterns)")
    print("=" * 60)
    
    agent = NLPAgent()
    
    test_cases = [
        {
            "name": "Réservation complète",
            "message": "Bonjour, je voudrais réserver une table pour demain soir à 20h pour 4 personnes. On aimerait une table en terrasse.",
            "check": {"guests": 4, "time": "20:00", "zone": "Terrasse"}
        },
        {
            "name": "Réservation avec budget",
            "message": "Bonjour, je cherche une table pour ce soir vers 19h30 pour 2 personnes, budget 30 USD.",
            "check": {"guests": 2, "time": "19:30", "budget": 30.0, "currency": "USD"}
        },
        {
            "name": "Message simple",
            "message": "Une table pour 4 personnes s'il vous plaît.",
            "check": {"guests": 4}
        },
        {
            "name": "Allergies",
            "message": "Je voudrais réserver pour 3 personnes, mon ami est allergique aux arachides.",
            "check": {"guests": 3, "allergies": ["arachides"]}
        },
        {
            "name": "Préférences",
            "message": "On veut manger du poisson, 5 personnes.",
            "check": {"guests": 5, "preferences": ["poisson"]}
        },
        {
            "name": "Occasion spéciale",
            "message": "i would like to order for 8 person at 20 p.m ",
            "check": {"guests": 8, "occasion": "anniversaire"}
                },
        
    ]
    
    success_count = 0
    total_checks = 0
    passed_checks = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n📌 Test {i}: {test['name']}")
        print(f"   Message: {test['message']}")
        
        try:
            extracted = agent._extract_with_patterns(test['message'])
            
            print(f"   Résultat:")
            print(f"     - Date: {extracted.date}")
            print(f"     - Heure: {extracted.time}")
            print(f"     - Couverts: {extracted.guests_count}")
            print(f"     - Préférences: {extracted.preferences}")
            print(f"     - Allergies: {extracted.allergies}")
            print(f"     - Budget: {extracted.budget} {extracted.currency}")
            print(f"     - Zone: {extracted.preferred_zone}")
            print(f"     - Occasion: {extracted.special_occasion}")
            print(f"     - Confiance: {extracted.confidence:.2f}")
            
            # Vérifier les champs attendus
            expected = test.get("check", {})
            test_passed = True
            
            if "guests" in expected:
                total_checks += 1
                if extracted.guests_count == expected["guests"]:
                    print(f"     ✅ Couverts: {extracted.guests_count}")
                    passed_checks += 1
                else:
                    print(f"     ❌ Couverts attendu: {expected['guests']}, obtenu: {extracted.guests_count}")
                    test_passed = False
            
            if "time" in expected:
                total_checks += 1
                if extracted.time == expected["time"]:
                    print(f"     ✅ Heure: {extracted.time}")
                    passed_checks += 1
                else:
                    print(f"     ❌ Heure attendue: {expected['time']}, obtenue: {extracted.time}")
                    test_passed = False
            
            if "budget" in expected:
                total_checks += 1
                if extracted.budget == expected["budget"]:
                    print(f"     ✅ Budget: {extracted.budget}")
                    passed_checks += 1
                else:
                    print(f"     ❌ Budget attendu: {expected['budget']}, obtenu: {extracted.budget}")
                    test_passed = False
            
            if "zone" in expected:
                total_checks += 1
                if extracted.preferred_zone == expected["zone"]:
                    print(f"     ✅ Zone: {extracted.preferred_zone}")
                    passed_checks += 1
                else:
                    print(f"     ❌ Zone attendue: {expected['zone']}, obtenue: {extracted.preferred_zone}")
                    test_passed = False
            
            if test_passed:
                success_count += 1
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"✅ Tests passés: {success_count}/{len(test_cases)}")
    print(f"✅ Vérifications passées: {passed_checks}/{total_checks}")
    print("=" * 60)
    
    return success_count == len(test_cases)


def main():
    """Exécute les tests."""
    success = test_nlp()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()