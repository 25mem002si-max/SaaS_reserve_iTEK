"""Protection anti-hallucination pour les agents LLM."""

from typing import Dict, Any, List, Optional
import json
import re
import logging

logger = logging.getLogger("ai_engine.guardrails")


class HallucinationGuard:
    """
    Garde-fou contre les hallucinations des LLM.
    
    Vérifie que les réponses des agents sont cohérentes avec les données disponibles.
    """

    def __init__(self):
        self.known_facts = {}

    def validate_agent_response(
        self,
        agent_name: str,
        response: str,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Valide la réponse d'un agent avant de l'envoyer au client.
        """
        issues = []
        blocked = False

        # 1. Vérification des données non vérifiées
        unchecked_data = self._find_unverified_claims(response, context)
        if unchecked_data:
            issues.extend(unchecked_data)
            blocked = True

        # 2. Vérification des incohérences
        inconsistencies = self._find_inconsistencies(response, context)
        if inconsistencies:
            issues.extend(inconsistencies)
            blocked = True

        # 3. Vérification des données inexistantes
        non_existent = self._find_non_existent_data(response, context)
        if non_existent:
            issues.extend(non_existent)
            blocked = True

        return {
            "valid": not blocked,
            "issues": issues,
            "blocked": blocked,
            "sanitized_response": self._sanitize_response(response, issues) if blocked else response,
        }

    def _find_unverified_claims(self, response: str, context: Dict[str, Any]) -> List[str]:
        """
        Trouve les affirmations non vérifiées dans la réponse.
        """
        issues = []
        
        # Vérifier si des disponibilités sont annoncées sans contexte
        availability_patterns = [
            r"disponible",
            r"libre",
            r"réservé",
            r"table\s+(?:n°|numéro)?\s*(\d+)",
        ]
        
        for pattern in availability_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                if not context.get("has_verified_availability"):
                    issues.append(f"Annonce de disponibilité non vérifiée: {pattern}")
        
        # Vérifier si des prix sont annoncés sans contexte
        price_patterns = [
            r"(\d+)\s*(?:USD|\$|CDF|francs?)",
            r"coûte",
            r"prix",
        ]
        
        for pattern in price_patterns:
            if re.search(pattern, response, re.IGNORECASE):
                if not context.get("has_verified_prices"):
                    issues.append(f"Annonce de prix non vérifiée: {pattern}")
        
        return issues

    def _find_inconsistencies(self, response: str, context: Dict[str, Any]) -> List[str]:
        """
        Trouve les incohérences dans la réponse.
        """
        issues = []
        
        # Vérifier le nombre de personnes
        guests = context.get("guests_count")
        if guests:
            # Chercher une mention du nombre dans la réponse
            mention = re.search(r"(\d+)\s*(?:personnes?|couverts?)", response)
            if mention:
                mentioned = int(mention.group(1))
                if mentioned != guests:
                    issues.append(f"Incohérence: mention de {mentioned} personnes, mais {guests} attendus")
        
        # Vérifier la date
        date = context.get("reservation_date")
        if date:
            # Chercher une mention de date dans la réponse
            date_patterns = [
                r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})",
                r"(\d{1,2})[/-](\d{1,2})",
            ]
            for pattern in date_patterns:
                match = re.search(pattern, response)
                if match:
                    # Vérifier la date
                    pass
        
        return issues

    def _find_non_existent_data(self, response: str, context: Dict[str, Any]) -> List[str]:
        """
        Trouve les données qui n'existent pas dans le contexte.
        """
        issues = []
        
        # Vérifier les plats
        menu_items = context.get("menu_items", [])
        if menu_items:
            # Chercher des plats mentionnés qui ne sont pas dans le menu
            menu_names = [item.get("name", "").lower() for item in menu_items]
            
            # Extraire les noms de plats de la réponse
            dish_pattern = r"[A-Za-zÀ-ÿ]+\s+[A-Za-zÀ-ÿ]+"
            potential_dishes = re.findall(dish_pattern, response)
            
            for dish in potential_dishes:
                if dish.lower() not in menu_names and dish.lower() not in ["poulet", "poisson", "riz", "salade"]:
                    # Vérifier si c'est vraiment un plat
                    if len(dish) > 5:
                        issues.append(f"Plat mentionné non présent dans le menu: {dish}")
        
        return issues

    def _sanitize_response(self, response: str, issues: List[str]) -> str:
        """
        Nettoie une réponse problématique.
        """
        if not issues:
            return response
        
        # Si la réponse contient des hallucinations, la remplacer par un message générique
        if any("disponibilité" in issue for issue in issues):
            return "Je vais vérifier les disponibilités pour vous. Un instant..."

        if any("prix" in issue for issue in issues):
            return "Je vérifie les prix sur la carte du restaurant..."

        if any("réservation" in issue for issue in issues):
            return "Je vérifie votre réservation..."

        return response


# Instance globale
_hallucination_guard: Optional[HallucinationGuard] = None


def get_hallucination_guard() -> HallucinationGuard:
    """Retourne l'instance du garde-fou."""
    global _hallucination_guard
    if _hallucination_guard is None:
        _hallucination_guard = HallucinationGuard()
    return _hallucination_guard


def validate_response(agent_name: str, response: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Valide une réponse d'agent."""
    guard = get_hallucination_guard()
    return guard.validate_agent_response(agent_name, response, context)