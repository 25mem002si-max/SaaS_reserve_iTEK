"""Agent Orchestrateur - Cerveau du système multi-agents."""

import json
import logging
import re
from typing import Optional

from app.services.llm_service import get_llm_service
from app.prompts.loader import load_prompt
from app.schemas.intent import Intent, IntentType
from app.graph.state import ConversationState, should_handoff
from app.config.settings import settings
from app.services.conversation_memory import get_conversation_memory_service

logger = logging.getLogger("ai_engine.agents.orchestrator")


class OrchestratorAgent:
    """Agent Orchestrateur - Détermine l'intention et route la conversation."""

    def __init__(self):
        self.llm = get_llm_service()
        self.prompt = load_prompt("orchestrator")
        self._use_llm = settings.use_llm
        self._llm_calls: dict[str, int] = {}

    def analyze(self, state: ConversationState) -> Intent:
        """Analyse l'intention du client à partir de l'état."""
        logger.info(f"🎯 Orchestrator - Conversation: {state.get('conversation_id')}")
        
        # Récupérer le dernier message utilisateur
        messages = state.get("messages", [])
        user_messages = [m for m in messages if m.role == "user"]
        
        if not user_messages:
            return Intent(
                type=IntentType.UNKNOWN,
                confidence=0.0,
                requires_clarification=True,
                clarification_question="Bonjour ! Comment puis-je vous aider ?"
            )
        
        last_message = user_messages[-1].content
        
        memory = get_conversation_memory_service()
        conversation_memory = memory.load_context(state.get("conversation_id", "unknown"))
        context_summary = conversation_memory.get("summary", "")

        # L'analyse rapide doit se faire sur le message courant pour éviter qu'un
        # mot clé du contexte historique ne force une mauvaise intention.
        intent = self._quick_analyze(
            last_message,
            state_has_reservation_context=bool(state.get("extracted_info") or state.get("reservation")),
        )
        
        # Si on a une confiance élevée, on retourne directement
        if intent.confidence >= 0.75:
            return intent
        
        # Sinon, essayer le LLM si disponible
        conversation_id = state.get("conversation_id", "unknown")
        if self._use_llm and self._llm_calls.get(conversation_id, 0) < settings.llm_max_calls_per_conversation:
            try:
                self._llm_calls[conversation_id] = self._llm_calls.get(conversation_id, 0) + 1
                llm_intent = self._analyze_with_llm(
                    f"{last_message}\nContexte_recent: {context_summary}",
                    state,
                )
                if llm_intent.confidence > intent.confidence:
                    return llm_intent
            except Exception as e:
                logger.warning(f"Erreur LLM orchestrator: {e}")
                if not settings.llm_fallback_enabled:
                    return Intent(type=IntentType.UNKNOWN, confidence=0.0, requires_clarification=True)
        
        return intent

    def _quick_analyze(self, message: str, state_has_reservation_context: bool = False) -> Intent:
        """Analyse améliorée avec des patterns plus précis."""
        text_lower = message.lower()

        cancellation_keywords = ["annuler", "annule", "annulation", "supprimer ma réservation"]
        modification_keywords = ["modifier", "changer", "déplacer", "reporter", "décaler"]
        confirmation_keywords = [
            "j'ai payé", "jai payé", "paiement effectué", "paiement réussi",
            "confirme ma réservation", "confirmer ma réservation", "c'est payé",
        ]

        if any(word in text_lower for word in cancellation_keywords):
            return Intent(type=IntentType.CANCEL_RESERVATION, confidence=0.98)

        if any(word in text_lower for word in modification_keywords) and "réservation" in text_lower:
            return Intent(type=IntentType.MODIFY_RESERVATION, confidence=0.96)

        if any(phrase in text_lower for phrase in confirmation_keywords):
            return Intent(type=IntentType.PAYMENT, confidence=0.96)
        
        # ============================================
        # 1. Vérifier d'abord si c'est une réservation (avant transfert humain)
        # ============================================
        is_reservation = any(word in text_lower for word in [
            "réserver", "réservation", "table", "restaurant", "place",
            "couvert", "personnes", "couverts"
        ]) or bool(re.fullmatch(r"\s*\d{1,2}\s*", text_lower))
        
        # ============================================
        # 2. TRANSFERT HUMAIN (uniquement si ce n'est pas une réservation)
        # ============================================
        handoff_keywords = [
            "humain", "manager", "gérant",
            "parler à quelqu'un", "parler à un humain",
            "contact humain", "assistance humaine"
        ]
        # NE PAS inclure "personne" car cela cause des faux positifs avec "X personnes"
        if any(word in text_lower for word in handoff_keywords) and not is_reservation:
            return Intent(
                type=IntentType.HUMAN_HANDOFF,
                confidence=0.98,
                requires_clarification=False,
            )
        
        # ============================================
        # 3. DISPONIBILITÉ (avant réservation si le client demande juste une disponibilité)
        # ============================================
        availability_keywords = [
            "disponible", "libre", "y a-t-il", "est-ce qu'il y a",
            "avez-vous", "quand", "créneau", "horaire", "table libre", "table disponible"
        ]
        if any(word in text_lower for word in availability_keywords):
            if not any(word in text_lower for word in ["réserver", "réservation", "je voudrais réserver", "je veux réserver"]):
                return Intent(
                    type=IntentType.CHECK_AVAILABILITY,
                    confidence=0.88,
                    requires_clarification=False,
                )

        # ============================================
        # 4. PAIEMENT
        # ============================================
        payment_keywords = [
            "paiement", "payer", "acompte", "dépôt",
            "payé", "mobile money", "mpesa", "orange money", "airtel money"
        ]
        if any(word in text_lower for word in payment_keywords):
            return Intent(
                type=IntentType.PAYMENT,
                confidence=0.92,
                requires_clarification=False,
            )
        
        # ============================================
        # 5. RECOMMANDATION
        # ============================================
        recommendation_keywords = [
            "recommand", "conseil", "suggér", "sugger",
            "plat", "menu", "spécialité", "signature"
        ]
        if any(word in text_lower for word in recommendation_keywords):
            if not any(word in text_lower for word in ["réserver", "réservation", "table"]):
                return Intent(
                    type=IntentType.GET_RECOMMENDATIONS,
                    confidence=0.88,
                    requires_clarification=False,
                )

        if any(word in text_lower for word in ["confirme", "confirmation", "validé", "valide"]):
            return Intent(type=IntentType.PAYMENT, confidence=0.82)
        
        # ============================================
        # 6. RÉSERVATION (priorité élevée)
        # ============================================
        if is_reservation or state_has_reservation_context:
            has_date = any(word in text_lower for word in [
                "demain", "aujourd'hui", "ce soir", "soir", 
                "jour", "date", "lundi", "mardi", "mercredi", 
                "jeudi", "vendredi", "samedi", "dimanche"
            ])
            has_guests = bool(re.search(r"\d+\s*(?:personnes?|couverts?|pax)", text_lower))
            has_time = bool(re.search(r"\d{1,2}h", text_lower))
            
            # Si toutes les informations sont présentes
            if has_date and has_guests and has_time:
                return Intent(
                    type=IntentType.NEW_RESERVATION,
                    confidence=0.95,
                    requires_clarification=False,
                )
            # Si certaines informations sont présentes
            elif has_date or has_guests:
                return Intent(
                    type=IntentType.NEW_RESERVATION,
                    confidence=0.80,
                    requires_clarification=True,
                    clarification_question=self._get_clarification_question(has_date, has_guests, has_time)
                )
            else:
                return Intent(
                    type=IntentType.NEW_RESERVATION,
                    confidence=0.70,
                    requires_clarification=True,
                    clarification_question="Pour combien de personnes et à quelle date souhaitez-vous réserver ?"
                )
        
        # ============================================
        # 7. SALUTATION
        # ============================================
        greeting_keywords = ["bonjour", "salut", "hello", "hi", "bonsoir", "coucou", "hey"]
        if any(word in text_lower for word in greeting_keywords):
            if not is_reservation:
                return Intent(
                    type=IntentType.GREETING,
                    confidence=0.95,
                    requires_clarification=False,
                )
        
        # ============================================
        # 8. AU REVOIR
        # ============================================
        goodbye_keywords = ["au revoir", "bye", "à bientôt", "merci", "aurevoir", "bonne journée"]
        if any(word in text_lower for word in goodbye_keywords):
            return Intent(
                type=IntentType.GOODBYE,
                confidence=0.90,
                requires_clarification=False,
            )
        
        # ============================================
        # 9. INTENTION NON RECONNUE
        # ============================================
        return Intent(
            type=IntentType.UNKNOWN,
            confidence=0.3,
            requires_clarification=True,
            clarification_question="Je n'ai pas bien compris. Pouvez-vous reformuler votre demande ?",
        )

    def _get_clarification_question(self, has_date: bool, has_guests: bool, has_time: bool) -> str:
        """Génère une question de clarification appropriée."""
        missing = []
        if not has_date:
            missing.append("la date")
        if not has_time:
            missing.append("l'heure")
        if not has_guests:
            missing.append("le nombre de personnes")
        
        if len(missing) == 1:
            return f"Pourriez-vous préciser {missing[0]} ?"
        elif len(missing) == 2:
            return f"Pourriez-vous préciser {missing[0]} et {missing[1]} ?"
        else:
            return "Pourriez-vous me donner la date, l'heure et le nombre de personnes ?"

    def _analyze_with_llm(self, message: str, state: ConversationState) -> Intent:
        """Analyse avec le LLM (désactivé par défaut)."""
        try:
            context = self._build_context(state)
            
            response = self.llm.invoke(
                system_prompt=self.prompt,
                user_message=f"Message du client: {message}\n\nContexte: {context}",
                temperature=0.1,
            )
            
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                return Intent(type=IntentType.UNKNOWN, confidence=0.3)
            
            data = json.loads(json_match.group())
            
            intent_map = {
                "NEW_RESERVATION": IntentType.NEW_RESERVATION,
                "CHECK_AVAILABILITY": IntentType.CHECK_AVAILABILITY,
                "GET_RECOMMENDATIONS": IntentType.GET_RECOMMENDATIONS,
                "MODIFY_RESERVATION": IntentType.MODIFY_RESERVATION,
                "CANCEL_RESERVATION": IntentType.CANCEL_RESERVATION,
                "PAYMENT": IntentType.PAYMENT,
                "HUMAN_HANDOFF": IntentType.HUMAN_HANDOFF,
                "GREETING": IntentType.GREETING,
                "GOODBYE": IntentType.GOODBYE,
                "CHITCHAT": IntentType.CHITCHAT,
                "UNKNOWN": IntentType.UNKNOWN,
            }
            
            return Intent(
                type=intent_map.get(data.get("intent", "UNKNOWN"), IntentType.UNKNOWN),
                confidence=data.get("confidence", 0.5),
                alternative_intents=[
                    intent_map.get(i, IntentType.UNKNOWN) 
                    for i in data.get("alternative_intents", [])
                ],
                requires_clarification=data.get("requires_clarification", False),
                clarification_question=data.get("clarification_question"),
            )
            
        except Exception as e:
            logger.warning(f"Erreur LLM orchestrator: {e}")
            return Intent(type=IntentType.UNKNOWN, confidence=0.3)

    def _build_context(self, state: ConversationState) -> str:
        """Construit le contexte pour le LLM."""
        context_lines = []
        
        reservation = state.get("reservation")
        if reservation:
            context_lines.append(f"Réservation en cours:")
            context_lines.append(f"  - Date: {reservation.date}")
            context_lines.append(f"  - Heure: {reservation.time}")
            context_lines.append(f"  - Couverts: {reservation.guests_count}")
        
        customer = state.get("customer")
        if customer:
            context_lines.append(f"Client: {customer.name or 'Inconnu'}")

        messages = state.get("messages", [])
        if messages:
            context_lines.append("Derniers échanges:")
            context_lines.extend(
                f"  - {message.role.value}: {message.content}"
                for message in messages[-6:]
            )
        
        return "\n".join(context_lines)


# Instance globale
_orchestrator_agent: Optional[OrchestratorAgent] = None


def get_orchestrator_agent() -> OrchestratorAgent:
    """Retourne l'instance de l'agent orchestrateur."""
    global _orchestrator_agent
    if _orchestrator_agent is None:
        _orchestrator_agent = OrchestratorAgent()
    return _orchestrator_agent


def analyze_intent(state: ConversationState) -> Intent:
    """Analyse l'intention à partir de l'état."""
    agent = get_orchestrator_agent()
    return agent.analyze(state)