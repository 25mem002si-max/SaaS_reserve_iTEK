#!/usr/bin/env python
"""Script pour tester l'Agent Recommandation."""

import sys
import uuid
from datetime import datetime, timedelta

sys.path.insert(0, ".")

print("=" * 60)
print("🔍 TEST DE L'AGENT RECOMMANDATION")
print("=" * 60)

try:
    from app.agents.recommendation_agent import get_recommendation_agent
    from app.schemas.recommendation import RecommendationRequest
    
    print("\n📌 Création de l'agent...")
    agent = get_recommendation_agent()
    print("   ✅ Agent créé")
    
    # Test 1: Recommandation simple
    print("\n📌 Test 1: Recommandation simple")
    request = RecommendationRequest(
        restaurant_id="rest-001",
        guests_count=4,
        preferences=["poisson", "local"],
        allergies=["arachides"],
        budget=20.0,
        currency="USD",
    )
    
    print(f"   - Préférences: {request.preferences}")
    print(f"   - Allergies: {request.allergies}")
    print(f"   - Budget: {request.budget} {request.currency}")
    
    result = agent.get_recommendations(request)
    
    print("\n📌 Résultat:")
    print(f"   - Message: {result.message}")
    print(f"   - Total estimé: {result.total_estimated_price} {result.currency}")
    print(f"   - Items recommandés: {len(result.items)}")
    
    for item in result.items:
        print(f"     • {item.name} - {item.price} {item.currency}")
        print(f"       {item.match_reason}")
    
    # Test 2: Avec occasion spéciale
    print("\n📌 Test 2: Avec occasion spéciale")
    request = RecommendationRequest(
        restaurant_id="rest-001",
        guests_count=2,
        preferences=["viande"],
        special_occasion="anniversaire",
        budget=30.0,
        currency="USD",
    )
    
    result = agent.get_recommendations(request)
    
    print(f"   - Occasion: {request.special_occasion}")
    print(f"   - Items recommandés: {len(result.items)}")
    
    print("\n✅ Tous les tests passés !")
    print("=" * 60)

except Exception as e:
    print(f"\n❌ Erreur: {e}")
    import traceback
    traceback.print_exc()