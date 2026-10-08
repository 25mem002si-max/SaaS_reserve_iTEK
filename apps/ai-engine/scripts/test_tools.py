#!/usr/bin/env python
"""Script pour tester les outils (Function Calling)."""

import sys
sys.path.insert(0, ".")

from app.tools import (
    CheckAvailabilityTool,
    LockTableTool,
    CreateReservationTool,
    GetRestaurantMenuTool,
)


def test_tools():
    """Teste tous les outils."""
    print("=" * 60)
    print("🔍 TEST DES OUTILS")
    print("=" * 60)
    
    tools = [
        ("CheckAvailabilityTool", CheckAvailabilityTool()),
        ("LockTableTool", LockTableTool()),
        ("CreateReservationTool", CreateReservationTool()),
        ("GetRestaurantMenuTool", GetRestaurantMenuTool()),
    ]
    
    for name, tool in tools:
        print(f"\n📌 Test: {name}")
        
        # Tester la conversion en dictionnaire
        try:
            schema = tool.to_dict()
            print(f"  ✅ Schéma OK - {schema['function']['name']}")
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
            continue
        
        # Tester l'exécution
        try:
            if name == "CheckAvailabilityTool":
                result = tool.execute(
                    restaurant_id="rest-001",
                    date="2026-08-25",
                    time="20:00",
                    guests_count=4,
                )
            elif name == "LockTableTool":
                result = tool.execute(
                    table_id="t1",
                    restaurant_id="rest-001",
                )
            elif name == "CreateReservationTool":
                result = tool.execute(
                    restaurant_id="rest-001",
                    table_id="t1",
                    customer_name="Jean Dupont",
                    customer_phone="+243123456789",
                    reservation_date="2026-08-25 20:00",
                    guests_count=4,
                )
            elif name == "GetRestaurantMenuTool":
                result = tool.execute(
                    restaurant_id="rest-001",
                )
            else:
                continue
            
            print(f"  ✅ Exécution OK: {result.message}")
            print(f"  ✅ Success: {result.success}")
            
        except Exception as e:
            print(f"  ❌ Erreur: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Test des outils terminé")
    print("=" * 60)


if __name__ == "__main__":
    test_tools()