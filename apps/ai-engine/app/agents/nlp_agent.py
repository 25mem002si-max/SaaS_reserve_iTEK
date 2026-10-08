"""Agent NLP - Extraction d'informations structurées."""

import json
import logging
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from app.services.llm_service import get_llm_service
from app.prompts.loader import load_prompt
from app.schemas.nlp import ExtractedInformation, NLPResult, MissingInformation
from app.guardrails.safety import get_safety_guard
from app.config.settings import settings

logger = logging.getLogger("ai_engine.agents.nlp")


class NLPAgent:
    """Agent NLP pour l'extraction d'informations."""
    
    def __init__(self):
        self.llm = get_llm_service()
        self.prompt = load_prompt("nlp")
        self._use_llm = settings.use_llm
        self._llm_calls: dict[str, int] = {}

    def extract(
        self,
        message: str,
        conversation_id: str = "unknown",
        conversation_context: str = "",
    ) -> ExtractedInformation:
        """Extrait les informations d'un message utilisateur."""
        message = get_safety_guard().sanitize_input(message)
        logger.info(f"🧠 NLP Extraction: {message[:100]}...")
        
        # 1. Essayer d'abord l'extraction par pattern (rapide)
        extracted = self._extract_with_patterns(message)
        
        # 2. Si les patterns ne suffisent pas, utiliser le LLM
        can_call_llm = self._llm_calls.get(conversation_id, 0) < settings.llm_max_calls_per_conversation
        if self._use_llm and can_call_llm and (not extracted.has_complete_reservation_info() or extracted.confidence < 0.7):
            try:
                self._llm_calls[conversation_id] = self._llm_calls.get(conversation_id, 0) + 1
                llm_extracted = self._extract_with_llm(message, conversation_context)
                extracted = self._merge_extractions(extracted, llm_extracted)
            except Exception as e:
                logger.warning(f"Erreur LLM, utilisation uniquement des patterns: {e}")
        
        return extracted

    def _extract_with_patterns(self, message: str) -> ExtractedInformation:
        """Extraction basique avec des expressions régulières."""
        text_lower = message.lower()
        
        # ---- Date ----
        date = None
        today = datetime.now().date()
        
        if "demain" in text_lower:
            date = today + timedelta(days=1)
        elif "aujourd'hui" in text_lower or "ce soir" in text_lower:
            date = today
        elif "après-demain" in text_lower:
            date = today + timedelta(days=2)
        else:
            # Chercher un format JJ/MM ou JJ/MM/AAAA
            date_match = re.search(r"(\d{1,2})[/-](\d{1,2})(?:[/-](\d{4}))?", message)
            if date_match:
                try:
                    day = int(date_match.group(1))
                    month = int(date_match.group(2))
                    year = int(date_match.group(3)) if date_match.group(3) else today.year
                    date = datetime(year, month, day).date()
                except ValueError:
                    pass

            months = {
                "janvier": 1, "février": 2, "fevrier": 2, "mars": 3,
                "avril": 4, "mai": 5, "juin": 6, "juillet": 7,
                "août": 8, "aout": 8, "septembre": 9, "octobre": 10,
                "novembre": 11, "décembre": 12, "decembre": 12,
            }
            month_pattern = "|".join(months)
            month_match = re.search(rf"(\d{{1,2}})\s+({month_pattern})(?:\s+(\d{{4}}))?", text_lower)
            if month_match:
                year = int(month_match.group(3)) if month_match.group(3) else today.year
                try:
                    date = datetime(year, months[month_match.group(2)], int(month_match.group(1))).date()
                except ValueError:
                    date = None

            # Chercher le prochain jour de la semaine mentionné.
            weekdays = {
                "lundi": 0, "mardi": 1, "mercredi": 2, "jeudi": 3,
                "vendredi": 4, "samedi": 5, "dimanche": 6,
            }
            for weekday, weekday_number in weekdays.items():
                if weekday in text_lower:
                    days_ahead = (weekday_number - today.weekday()) % 7
                    date = today + timedelta(days=days_ahead or 7)
                    break
        
        # ---- Heure ----
        time = None
        time_match = re.search(r"(\d{1,2})h(?:\s*(\d{1,2}))?", message, flags=re.IGNORECASE)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2)) if time_match.group(2) else 0
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                time = f"{hour:02d}:{minute:02d}"
        else:
            time_match = re.search(r"(\d{1,2})\s*[:.]?\s*(\d{2})", message)
            if time_match:
                time = f"{int(time_match.group(1)):02d}:{time_match.group(2)}"
            else:
                time_match = re.search(r"(\d{1,2})\s*(?:p\.m\.?|pm|a\.m\.?|am)", message, flags=re.IGNORECASE)
                if time_match:
                    hour = int(time_match.group(1))
                    if hour == 12:
                        hour = 0
                    elif hour < 12:
                        hour = hour
                    time = f"{hour:02d}:00"
                if time is None and any(term in text_lower for term in ["dans la soirée", "ce soir", "ce soir-là"]):
                    time = "19:00"
        
        # ---- Nombre de personnes (AMÉLIORÉ) ----
        guests = None
        
        # Patterns pour "pour X personnes", "X personnes", etc.
        people_patterns = [
            r"(\d+)\s*(?:personnes?|persons?|people|couverts?|pax)",  # 4 personnes, 8 person
            r"(?:pour|à|for|at)\s*(\d+)\s*(?:personnes?|persons?|people|couverts?|pax)?",  # pour 4, for 8 person
            r"on\s*(?:sera|est)\s*(\d+)",             # on sera 8, on est 8
            r"nous\s*(?:serons|sommes)\s*(\d+)",      # nous serons 8, nous sommes 8
            r"(\d+)\s*(?:personnes?|persons?|people)\s*(?:s'il vous plaît)?",  # 4 personnes s'il vous plaît
        ]
        
        for pattern in people_patterns:
            match = re.search(pattern, text_lower)
            if match:
                guests = int(match.group(1))
                break
        if guests is None:
            single_number = re.fullmatch(r"\s*(\d{1,2})\s*", text_lower)
            if single_number:
                guests = int(single_number.group(1))
        if guests is None and any(term in text_lower for term in ["un couple", "en couple"]):
            guests = 2
        
        # ---- Préférences ----
        preferences = []
        pref_keywords = {
            "poisson": "poisson",
            "viande": "viande",
            "végétarien": "végétarien",
            "végétalien": "végétalien",
            "sans gluten": "sans gluten",
            "halal": "halal",
            "local": "cuisine locale",
            "congolais": "cuisine congolaise",
        }
        for key, value in pref_keywords.items():
            if key in text_lower:
                preferences.append(value)
        
        # ---- Allergies ----
        allergies = []
        allergy_keywords = {
            "arachide": "arachides",
            "cacahuète": "arachides",
            "gluten": "gluten",
            "lactose": "lactose",
            "lait": "lactose",
            "fruits de mer": "fruits de mer",
            "crustacés": "crustacés",
            "noix": "noix",
            "œuf": "œufs",
            "oeuf": "œufs",
        }
        for key, value in allergy_keywords.items():
            if key in text_lower:
                allergies.append(value)
        
        # ---- Budget ----
        budget = None
        budget_match = re.search(r"(\d+)\s*(?:USD|\$|CDF|francs?)", message)
        if budget_match:
            budget = float(budget_match.group(1))
        
        # ---- Devise ----
        currency = None
        if "USD" in message or "$" in message:
            currency = "USD"
        elif "CDF" in message or "francs" in message:
            currency = "CDF"
        
        # ---- Zone préférée ----
        zone = None
        zone_keywords = {
            "terrasse": "Terrasse",
            "vip": "VIP",
            "intérieur": "Intérieur",
            "interieur": "Intérieur",
            "calme": "Intérieur",
            "tranquille": "Intérieur",
            "jardin": "Terrasse",
            "extérieur": "Terrasse",
            "exterieur": "Terrasse",
        }
        for key, value in zone_keywords.items():
            if key in text_lower:
                zone = value
                break
        
        # ---- Occasion spéciale ----
        occasion = None
        occasion_keywords = {
            "anniversaire": "anniversaire",
            "mariage": "anniversaire de mariage",
            "rendez-vous galant": "rencontre",
            "dîner en amoureux": "rencontre",
            "affaire": "dîner d'affaires",
            "business": "dîner d'affaires",
        }
        for key, value in occasion_keywords.items():
            if key in text_lower:
                occasion = value
                break
        
        # ---- Calcul de la confiance ----
        confidence = 0.5
        confidence += 0.1 if date else 0
        confidence += 0.1 if time else 0
        confidence += 0.1 if guests else 0
        confidence += 0.05 if preferences else 0
        confidence += 0.05 if allergies else 0
        
        return ExtractedInformation(
            date=datetime.combine(date, datetime.min.time()) if date else None,
            time=time,
            guests_count=guests,
            preferences=list(set(preferences)),
            allergies=list(set(allergies)),
            budget=budget,
            currency=currency,
            preferred_zone=zone,
            special_occasion=occasion,
            raw_text=message,
            confidence=min(confidence, 0.95),
        )

    def _extract_with_llm(self, message: str, conversation_context: str = "") -> ExtractedInformation:
        """Extraction avec le LLM."""
        try:
            response = self.llm.invoke(
                system_prompt=self.prompt,
                user_message=(
                    f"Contexte de conversation déjà connu:\n{conversation_context}\n\n"
                    f"Nouveau message:\n{message}"
                ),
                temperature=0.1,
            )
            
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                logger.warning("Aucun JSON trouvé dans la réponse LLM")
                return ExtractedInformation(raw_text=message, confidence=0.3)
            
            data = json.loads(json_match.group())
            
            date = None
            if data.get("date"):
                try:
                    date = datetime.fromisoformat(data["date"])
                except ValueError:
                    pass
            
            return ExtractedInformation(
                date=date,
                time=data.get("time"),
                guests_count=data.get("guests_count"),
                preferences=data.get("preferences", []),
                allergies=data.get("allergies", []),
                budget=data.get("budget"),
                currency=data.get("currency"),
                preferred_zone=data.get("preferred_zone"),
                special_occasion=data.get("special_occasion"),
                raw_text=message,
                confidence=data.get("confidence", 0.7),
            )
            
        except Exception as e:
            logger.warning(f"Erreur extraction LLM: {e}")
            return ExtractedInformation(raw_text=message, confidence=0.3)

    def _merge_extractions(
        self,
        pattern: ExtractedInformation,
        llm: ExtractedInformation
    ) -> ExtractedInformation:
        """Fusionne les extractions pattern et LLM."""
        return ExtractedInformation(
            date=pattern.date or llm.date,
            time=pattern.time or llm.time,
            guests_count=pattern.guests_count or llm.guests_count,
            preferences=list(set(pattern.preferences + llm.preferences)),
            allergies=list(set(pattern.allergies + llm.allergies)),
            budget=pattern.budget or llm.budget,
            currency=pattern.currency or llm.currency,
            preferred_zone=pattern.preferred_zone or llm.preferred_zone,
            special_occasion=pattern.special_occasion or llm.special_occasion,
            raw_text=pattern.raw_text,
            confidence=max(pattern.confidence, llm.confidence),
        )

    def get_nlp_result(self, extracted: ExtractedInformation) -> NLPResult:
        """Crée un NLPResult à partir de l'extraction."""
        return NLPResult.from_extracted(extracted)


# Instance globale
_nlp_agent: Optional[NLPAgent] = None


def get_nlp_agent() -> NLPAgent:
    """Retourne l'instance de l'agent NLP."""
    global _nlp_agent
    if _nlp_agent is None:
        _nlp_agent = NLPAgent()
    return _nlp_agent


def process_message(
    message: str,
    conversation_id: str = "unknown",
    conversation_context: str = "",
) -> NLPResult:
    """Traite un message utilisateur complet."""
    agent = get_nlp_agent()
    extracted = agent.extract(
        message,
        conversation_id=conversation_id,
        conversation_context=conversation_context,
    )
    return agent.get_nlp_result(extracted)