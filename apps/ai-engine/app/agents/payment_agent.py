"""Agent Paiement - Gestion des paiements Mobile Money."""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from app.services.llm_service import get_llm_service
from app.prompts.loader import load_prompt
from app.schemas.payment import PaymentRequest, PaymentResult, PaymentStatus, PaymentProvider
from app.graph.state import ConversationState
from app.config.settings import settings
from app.services.backend_client import BackendClient
from app.services.supervision import get_agent_monitor

logger = logging.getLogger("ai_engine.agents.payment")


class PaymentAgent:
    """Agent Paiement - Gère les paiements Mobile Money."""

    def __init__(self):
        self.llm = get_llm_service()
        self.prompt = load_prompt("payment")
        self.backend = BackendClient()

    def create_payment_request(
        self,
        reservation_id: str,
        restaurant_id: str,
        amount: float,
        currency: str,
        phone_number: str,
        provider: str,
    ) -> Optional[PaymentResult]:
        """
        Crée une demande de paiement Mobile Money.
        
        NOTE: Cette fonction utilise le backend (Dev2).
        Pour l'instant, simule le paiement.
        """
        logger.info(f"💰 Création paiement - {reservation_id}, {amount} {currency}")
        
        request = PaymentRequest(
            reservation_id=reservation_id,
            restaurant_id=restaurant_id,
            amount=amount,
            currency=currency,
            phone_number=phone_number,
            provider=PaymentProvider(provider),
        )

        if settings.backend_enabled:
            response = self.backend.create_payment(request.model_dump(mode="json"))
            return PaymentResult.model_validate(response)

        # En local, un paiement Mobile Money reste en attente de confirmation.
        return PaymentResult(
            payment_id=f"pay-local-{datetime.now().strftime('%Y%m%d%H%M%S%f')}",
            reservation_id=reservation_id,
            status=PaymentStatus.PENDING,
            amount=amount,
            currency=currency,
            provider=request.provider,
            provider_reference=f"ref-local-{reservation_id}",
            message="Demande de paiement simulée. Confirmez-la sur votre téléphone.",
        )


    def get_payment_status(self, payment_id: str) -> Optional[PaymentResult]:
        """
        Vérifie le statut d'un paiement.
        
        NOTE: Cette fonction utilise le backend (Dev2).
        """
        logger.info(f"🔍 Vérification paiement - {payment_id}")
        
        if settings.backend_enabled:
            response = self.backend.get_payment_status(payment_id)
            return PaymentResult.model_validate(response)
        
        return PaymentResult(
            payment_id=payment_id,
            reservation_id="res-001",
            status=PaymentStatus.PENDING,
            amount=10.0,
            currency="USD",
            provider=PaymentProvider.M_PESA,
            message="Paiement en cours de traitement",
        )

    def process_payment(self, state: ConversationState) -> Dict[str, Any]:
        """
        Processus complet de paiement.
        """
        logger.info(f"💰 Processus paiement - {state.get('conversation_id')}")
        get_agent_monitor().record(
            "payment_started",
            conversation_id=state.get("conversation_id"),
            restaurant_id=state.get("restaurant_id"),
        )
        
        # 1. Récupérer la réservation
        reservation = state.get("reservation")
        if not reservation:
            return {
                "error": "Aucune réservation associée au paiement",
                "next_action": "error",
            }

        existing_payment = state.get("payment")
        last_message = state.get("messages", [])[-1].content.lower() if state.get("messages") else ""
        confirms_payment = any(phrase in last_message for phrase in [
            "j'ai payé", "jai payé", "paiement effectué", "paiement réussi", "c'est payé",
        ])
        if existing_payment and existing_payment.is_pending() and confirms_payment:
            status = self.get_payment_status(existing_payment.payment_id)
            if status and status.is_successful():
                return {
                    "payment": status,
                    "payment_required": False,
                    "waiting_for_payment": False,
                    "next_action": "confirmation",
                    "message": f"✅ Paiement de {status.amount} {status.currency} confirmé !",
                    "is_complete": True,
                }
            return {
                "payment": existing_payment,
                "waiting_for_payment": True,
                "next_action": "waiting_for_payment",
                "message": "Je vérifie votre paiement. Il est encore en attente de confirmation par le service Mobile Money.",
            }

        if existing_payment and existing_payment.is_pending():
            asks_how_to_pay = any(phrase in last_message for phrase in [
                "comment dois-je payer", "comment je paie", "comment payer",
                "comment effectuer", "que dois-je faire pour payer",
            ])
            if asks_how_to_pay:
                provider_name = {
                    PaymentProvider.M_PESA: "M-Pesa",
                    PaymentProvider.ORANGE_MONEY: "Orange Money",
                    PaymentProvider.AIRTEL_MONEY: "Airtel Money",
                }.get(existing_payment.provider, "votre service Mobile Money")
                return {
                    "payment": existing_payment,
                    "waiting_for_payment": True,
                    "next_action": "waiting_for_payment",
                    "message": (
                        f"Pour payer l'acompte de {existing_payment.amount} "
                        f"{existing_payment.currency}, ouvrez {provider_name} sur votre téléphone "
                        "et validez la demande qui vient de s'afficher. "
                        "Ne partagez jamais votre code PIN. Quand c'est fait, répondez simplement : « j'ai payé » "
                        "et je vérifierai le statut."
                    ),
                }
            return {
                "payment": existing_payment,
                "waiting_for_payment": True,
                "next_action": "waiting_for_payment",
                "message": f"⏳ Une demande de paiement de {existing_payment.amount} {existing_payment.currency} est déjà en cours. Veuillez la confirmer sur votre téléphone.",
            }
        
        # 2. Récupérer le client
        customer = state.get("customer")
        if not customer or not customer.phone:
            return {
                "error": "Numéro de téléphone client manquant",
                "next_action": "ask_phone",
                "message": "Pour effectuer le paiement, veuillez me donner votre numéro de téléphone Mobile Money.",
            }
        
        # 3. Déterminer le montant
        amount = reservation.deposit_amount or 10.0
        currency = reservation.currency or "USD"
        
        # 4. Déterminer le fournisseur (par défaut M-Pesa)
        provider = "m_pesa"

        # 5. Récupérer l'identifiant de réservation depuis un objet ou un dictionnaire
        reservation_confirmation = state.get("reservation_confirmation")
        if reservation_confirmation is None:
            reservation_id = "res-001"
        elif hasattr(reservation_confirmation, "reservation_id"):
            reservation_id = reservation_confirmation.reservation_id
        elif isinstance(reservation_confirmation, dict):
            reservation_id = reservation_confirmation.get("reservation_id", "res-001")
        else:
            reservation_id = "res-001"
        
        # 6. Créer le paiement
        payment_result = self.create_payment_request(
            reservation_id=reservation_id,
            restaurant_id=state.get("restaurant_id", "unknown"),
            amount=amount,
            currency=currency,
            phone_number=customer.phone,
            provider=provider,
        )
        
        if not payment_result:
            return {
                "error": "Échec de la création du paiement",
                "next_action": "retry",
                "message": "Désolé, le paiement n'a pas pu être initié. Voulez-vous réessayer ?",
            }
        
        # 6. Gérer le résultat
        if payment_result.is_successful():
            get_agent_monitor().record(
                "payment_succeeded",
                conversation_id=state.get("conversation_id"),
                restaurant_id=state.get("restaurant_id"),
                payment_id=payment_result.payment_id,
            )
            return {
                "payment": payment_result,
                "payment_required": False,
                "next_action": "confirmation",
                "message": f"✅ Paiement de {payment_result.amount} {payment_result.currency} confirmé !",
                "is_complete": True,
            }
        elif payment_result.is_pending():
            return {
                "payment": payment_result,
                "waiting_for_payment": True,
                "next_action": "waiting_for_payment",
                "message": f"⏳ Demande de paiement de {payment_result.amount} {payment_result.currency} envoyée. Veuillez confirmer sur votre téléphone.",
            }
        else:
            return {
                "payment": payment_result,
                "next_action": "retry_or_handoff",
                "message": "❌ Le paiement a échoué. Voulez-vous réessayer ou parler à un humain ?",
            }


# Instance globale
_payment_agent: Optional[PaymentAgent] = None


def get_payment_agent() -> PaymentAgent:
    """Retourne l'instance de l'agent paiement."""
    global _payment_agent
    if _payment_agent is None:
        _payment_agent = PaymentAgent()
    return _payment_agent


def process_payment(state: ConversationState) -> Dict[str, Any]:
    """Traite un paiement."""
    agent = get_payment_agent()
    return agent.process_payment(state)