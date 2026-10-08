"""Agent Recommandation - Recommande des plats selon les préférences."""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.services.llm_service import get_llm_service
from app.prompts.loader import load_prompt
from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResult,
    RecommendedItem,
)
from app.graph.state import ConversationState

logger = logging.getLogger("ai_engine.agents.recommendation")


class RecommendationAgent:
    """Agent Recommandation - Recommande des plats adaptés aux préférences."""

    def __init__(self):
        self.llm = get_llm_service()
        self.prompt = load_prompt("recommendation")

    def get_menu(self, restaurant_id: str) -> Dict[str, Any]:
        """
        Récupère le menu du restaurant.
        
        NOTE: Cette fonction utilise le backend (Dev2).
        Pour l'instant, simule un menu.
        """
        logger.info(f"📋 Récupération menu - {restaurant_id}")
        
        # TODO: Appeler le backend Dev2
        # Pour l'instant, simulation
        return {
            "restaurant_id": restaurant_id,
            "currency": "USD",
            "categories": [
                {
                    "id": "entrees",
                    "name": "Entrées",
                    "items": [
                        {"id": "e1", "name": "Salade Congolaise", "price": 8.0, "description": "Salade fraîche avec avocat, tomate et œuf", "category": "entree"},
                        {"id": "e2", "name": "Beignets de Banane", "price": 6.0, "description": "Beignets de banane plantain, croustillants", "category": "entree"},
                        {"id": "e3", "name": "Brochettes de Poisson", "price": 9.0, "description": "Brochettes de poisson grillé, marinées", "category": "entree"},
                    ]
                },
                {
                    "id": "plats",
                    "name": "Plats Principaux",
                    "items": [
                        {"id": "p1", "name": "Poulet Yassa", "price": 12.0, "description": "Poulet mariné au citron et oignons, servi avec riz", "category": "plat"},
                        {"id": "p2", "name": "Poisson Braisé", "price": 15.0, "description": "Poisson frais braisé avec légumes de saison", "category": "plat"},
                        {"id": "p3", "name": "Riz à la Viande", "price": 10.0, "description": "Riz parfumé avec morceaux de viande", "category": "plat"},
                        {"id": "p4", "name": "Mafé", "price": 13.0, "description": "Ragoût de viande à la sauce arachide", "category": "plat"},
                        {"id": "p5", "name": "Poisson à la Vapeur", "price": 14.0, "description": "Poisson cuit à la vapeur avec herbes", "category": "plat"},
                    ]
                },
                {
                    "id": "desserts",
                    "name": "Desserts",
                    "items": [
                        {"id": "d1", "name": "Fruit de Saison", "price": 4.0, "description": "Assortiment de fruits frais de saison", "category": "dessert"},
                        {"id": "d2", "name": "Gâteau au Chocolat", "price": 5.0, "description": "Gâteau fondant au chocolat", "category": "dessert"},
                        {"id": "d3", "name": "Sorbet Maison", "price": 4.0, "description": "Sorbet artisanal aux fruits", "category": "dessert"},
                    ]
                },
                {
                    "id": "boissons",
                    "name": "Boissons",
                    "items": [
                        {"id": "b1", "name": "Jus de Fruit", "price": 3.0, "description": "Jus frais de fruits", "category": "boisson"},
                        {"id": "b2", "name": "Soda", "price": 2.0, "description": "Boisson gazeuse", "category": "boisson"},
                        {"id": "b3", "name": "Bière Locale", "price": 4.0, "description": "Bière artisanale congolaise", "category": "boisson"},
                        {"id": "b4", "name": "Eau Minérale", "price": 1.5, "description": "Eau de source", "category": "boisson"},
                    ]
                }
            ]
        }

    def filter_by_allergies(self, items: List[Dict], allergies: List[str]) -> List[Dict]:
        """Filtre les plats qui contiennent des allergies."""
        if not allergies:
            return items
        
        filtered = []
        for item in items:
            # Vérifier si le plat contient une allergie
            has_allergy = False
            item_name = item.get("name", "").lower()
            item_desc = item.get("description", "").lower()
            
            for allergy in allergies:
                allergy_lower = allergy.lower()
                if allergy_lower in item_name or allergy_lower in item_desc:
                    has_allergy = True
                    break
            
            if not has_allergy:
                filtered.append(item)
        
        return filtered

    def filter_by_preferences(self, items: List[Dict], preferences: List[str]) -> List[Dict]:
        """Filtre les plats selon les préférences."""
        if not preferences:
            return items
        
        filtered = []
        for item in items:
            item_name = item.get("name", "").lower()
            item_desc = item.get("description", "").lower()
            
            for pref in preferences:
                pref_lower = pref.lower()
                if pref_lower in item_name or pref_lower in item_desc:
                    filtered.append(item)
                    break
        
        # Si aucun plat ne correspond, retourner tous les plats
        return filtered if filtered else items

    def filter_by_budget(self, items: List[Dict], budget: float) -> List[Dict]:
        """Filtre les plats selon le budget."""
        if not budget:
            return items
        
        return [item for item in items if item.get("price", 0) <= budget]

    def get_recommendations(self, request: RecommendationRequest) -> RecommendationResult:
        """
        Génère des recommandations de plats.
        """
        logger.info(f"🍽️ Recommandation - {request.restaurant_id}, {request.guests_count} personnes")
        
        # 1. Récupérer le menu
        menu = self.get_menu(request.restaurant_id)
        
        # 2. Extraire tous les items du menu
        all_items = []
        for category in menu.get("categories", []):
            for item in category.get("items", []):
                item["category_name"] = category.get("name", "")
                all_items.append(item)
        
        # 3. Appliquer les filtres
        filtered_items = all_items
        
        # Filtrer par allergies
        if request.allergies:
            filtered_items = self.filter_by_allergies(filtered_items, request.allergies)
        
        # Filtrer par préférences
        if request.preferences:
            filtered_items = self.filter_by_preferences(filtered_items, request.preferences)
        
        # Filtrer par budget
        if request.budget:
            filtered_items = self.filter_by_budget(filtered_items, request.budget)
        
        # 4. Sélectionner les meilleurs plats
        recommended_items = []
        
        # Sélectionner par catégorie
        categories = ["entree", "plat", "dessert", "boisson"]
        for category in categories:
            category_items = [item for item in filtered_items if item.get("category") == category]
            if category_items:
                # Prendre le premier ou le plus populaire
                recommended = category_items[0]
                recommended_items.append(RecommendedItem(
                    id=recommended.get("id", ""),
                    name=recommended.get("name", ""),
                    category=recommended.get("category_name", category),
                    description=recommended.get("description", ""),
                    price=recommended.get("price", 0),
                    currency=menu.get("currency", "USD"),
                    match_reason=self._get_match_reason(recommended, request),
                ))
        
        # Si pas assez de recommandations, compléter avec d'autres plats
        while len(recommended_items) < 3 and filtered_items:
            for item in filtered_items:
                if not any(r.id == item.get("id") for r in recommended_items):
                    recommended_items.append(RecommendedItem(
                        id=item.get("id", ""),
                        name=item.get("name", ""),
                        category=item.get("category_name", "plat"),
                        description=item.get("description", ""),
                        price=item.get("price", 0),
                        currency=menu.get("currency", "USD"),
                        match_reason=self._get_match_reason(item, request),
                    ))
                    break
        
        # 5. Calculer le total
        total = sum(item.price for item in recommended_items) * request.guests_count
        
        # 6. Générer le message
        message = self._generate_message(request, recommended_items)
        
        return RecommendationResult(
            restaurant_id=request.restaurant_id,
            items=recommended_items,
            total_estimated_price=total,
            currency=menu.get("currency", "USD"),
            message=message,
        )

    def _get_match_reason(self, item: Dict, request: RecommendationRequest) -> str:
        """Génère une raison pour la recommandation."""
        reasons = []
        
        if request.preferences:
            for pref in request.preferences:
                if pref.lower() in item.get("name", "").lower() or pref.lower() in item.get("description", "").lower():
                    reasons.append(f"Correspond à votre préférence pour {pref}")
                    break
        
        if request.special_occasion:
            reasons.append(f"Idéal pour {request.special_occasion}")
        
        if request.budget and item.get("price", 0) <= request.budget:
            reasons.append("Dans votre budget")
        
        if not reasons:
            reasons.append("Plat populaire de notre carte")
        
        return ", ".join(reasons)

    def _generate_message(self, request: RecommendationRequest, items: List[RecommendedItem]) -> str:
        """Génère un message d'introduction pour les recommandations."""
        parts = ["🍽️ Voici nos recommandations pour vous :"]
        
        if request.special_occasion:
            parts.append(f"🎉 Pour votre {request.special_occasion}")
        
        if request.preferences:
            parts.append(f"📌 Basé sur vos préférences : {', '.join(request.preferences)}")
        
        if request.allergies:
            parts.append(f"⚠️ Sans : {', '.join(request.allergies)}")
        
        return " ".join(parts)

    def process_recommendation(self, state: ConversationState) -> Dict[str, Any]:
        """
        Processus complet de recommandation.
        """
        logger.info(f"🍽️ Processus recommandation - {state.get('conversation_id')}")
        
        # Récupérer les informations
        extracted = state.get("extracted_info")
        reservation = state.get("reservation")
        
        # Créer la requête
        request = RecommendationRequest(
            restaurant_id=state.get("restaurant_id", "unknown"),
            guests_count=reservation.guests_count if reservation else 2,
            preferences=extracted.preferences if extracted else [],
            allergies=extracted.allergies if extracted else [],
            budget=extracted.budget if extracted else None,
            currency=(extracted.currency or "USD") if extracted else "USD",
            special_occasion=extracted.special_occasion if extracted else None,
        )
        
        # Obtenir les recommandations
        result = self.get_recommendations(request)
        
        return {
            "recommendation": result,
            "current_agent": "recommendation_agent",
            "next_action": "response",
            "message": result.get_recommendation_text(),
        }


# Instance globale
_recommendation_agent: Optional[RecommendationAgent] = None


def get_recommendation_agent() -> RecommendationAgent:
    """Retourne l'instance de l'agent recommandation."""
    global _recommendation_agent
    if _recommendation_agent is None:
        _recommendation_agent = RecommendationAgent()
    return _recommendation_agent


def process_recommendation(state: ConversationState) -> Dict[str, Any]:
    """Traite une demande de recommandation."""
    agent = get_recommendation_agent()
    return agent.process_recommendation(state)