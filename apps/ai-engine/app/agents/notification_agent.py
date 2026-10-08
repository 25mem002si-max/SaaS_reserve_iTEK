"""Agent Notification - Envoi des confirmations et rappels."""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import json

from app.services.llm_service import get_llm_service
from app.prompts.loader import load_prompt
from app.schemas.notification import (
    NotificationRequest,
    NotificationResult,
    NotificationType,
    NotificationChannel,
)
from app.schemas.reservation import ReservationConfirmation
from app.graph.state import ConversationState

logger = logging.getLogger("ai_engine.agents.notification")


class NotificationAgent:
    """Agent Notification - Gère les confirmations et rappels."""

    def __init__(self):
        self.llm = get_llm_service()
        self.prompt = load_prompt("notification")

    def generate_confirmation(
        self,
        reservation_id: str,
        reservation_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Génère un reçu PDF avec QR Code.
        
        NOTE: Cette fonction utilise le backend (Dev2).
        Pour l'instant, simule la génération.
        """
        logger.info(f"📄 Génération reçu - {reservation_id}")
        
        # TODO: Appeler le backend Dev2 pour générer PDF/QR
        # Pour l'instant, simulation
        
        return {
            "pdf_url": f"https://api.restaurant.com/receipts/{reservation_id}.pdf",
            "qr_code_token": f"qr-{reservation_id}",
            "qr_code_url": f"https://api.restaurant.com/qr/{reservation_id}",
            "message": "Reçu généré avec succès",
        }

    def send_notification(
        self,
        notification_type: str,
        recipient: str,
        channel: str,
        template_data: Dict[str, Any],
    ) -> bool:
        """
        Envoie une notification.
        
        NOTE: Cette fonction utilise le backend (Dev2) ou Celery.
        """
        logger.info(f"📨 Envoi notification - {notification_type} via {channel}")
        
        # TODO: Appeler le backend Dev2 ou Celery
        # Pour l'instant, simulation
        import random
        return random.random() > 0.1  # 90% de chance de succès

    def format_confirmation_message(self, confirmation: ReservationConfirmation) -> str:
        """
        Formate le message de confirmation pour le client.
        """
        status_emoji = "✅" if confirmation.status.value == "CONFIRMED" else "⏳"
        status_text = "confirmée" if confirmation.status.value == "CONFIRMED" else "en attente de paiement"
        
        lines = [
            f"{status_emoji} Réservation {status_text} !",
            "",
            f"📅 Date: {confirmation.date.strftime('%d/%m/%Y')}",
            f"⏰ Heure: {confirmation.date.strftime('%H:%M')}",
            f"👥 {confirmation.guests_count} personnes",
            f"📍 Table: {confirmation.table_label}",
            f"🆔 Réf: {confirmation.reservation_id}",
        ]
        
        if confirmation.deposit_amount > 0:
            lines.append(f"💰 Acompte: {confirmation.deposit_amount} {confirmation.currency}")
            if confirmation.deposit_paid:
                lines.append("✅ Acompte payé")
            else:
                lines.append("⏳ Acompte en attente de paiement")
        
        lines.append("")
        lines.append("📱 Un QR Code vous sera envoyé pour l'entrée.")
        lines.append("À très bientôt !")
        
        return "\n".join(lines)

    def process_notification(self, state: ConversationState) -> Dict[str, Any]:
        """
        Processus complet de notification.
        """
        logger.info(f"📨 Processus notification - {state.get('conversation_id')}")
        
        # 1. Récupérer la confirmation
        confirmation = state.get("reservation_confirmation")
        if not confirmation:
            return {
                "error": "Aucune confirmation de réservation",
                "next_action": "error",
            }
        
        # 2. Récupérer le client
        customer = state.get("customer")
        if not customer:
            return {
                "error": "Client non trouvé",
                "next_action": "error",
            }
        
        # 3. Générer le reçu PDF
        receipt = self.generate_confirmation(
            reservation_id=confirmation.reservation_id,
            reservation_data={
                "customer_name": confirmation.customer_name,
                "date": confirmation.date.isoformat(),
                "guests_count": confirmation.guests_count,
                "table_label": confirmation.table_label,
            },
        )
        
        # 4. Mettre à jour la confirmation avec les informations du reçu
        confirmation.qr_code_token = receipt.get("qr_code_token")
        confirmation.pdf_url = receipt.get("pdf_url")
        
        # 5. Formater le message
        message = self.format_confirmation_message(confirmation)
        
        # 6. Envoyer la notification WhatsApp
        if customer.phone:
            whatsapp_sent = self.send_notification(
                notification_type="confirmation",
                recipient=customer.phone,
                channel="whatsapp",
                template_data={
                    "message": message,
                    "pdf_url": receipt.get("pdf_url"),
                    "qr_code_url": receipt.get("qr_code_url"),
                },
            )
        else:
            whatsapp_sent = False
        
        # 7. Envoyer la notification par chat (toujours)
        chat_sent = self.send_notification(
            notification_type="confirmation",
            recipient=state.get("conversation_id", "unknown"),
            channel="chat",
            template_data={
                "message": message,
            },
        )
        
        # 8. Planifier les rappels
        reminder_scheduled = self.schedule_reminders(confirmation, customer)
        
        # 9. Retourner le résultat
        return {
            "notification_sent": whatsapp_sent or chat_sent,
            "reminder_scheduled": reminder_scheduled,
            "message": message,
            "receipt": receipt,
            "is_complete": True,
            "next_action": "end",
            "current_agent": "notification_agent",
        }

    def schedule_reminders(
        self,
        confirmation: ReservationConfirmation,
        customer: Any,
    ) -> bool:
        """
        Planifie les rappels H-24 et H-2.
        
        NOTE: Cette fonction utilise Celery (Dev2).
        """
        logger.info(f"⏰ Planification rappels - {confirmation.reservation_id}")
        
        # TODO: Utiliser Celery via Dev2
        # Pour l'instant, simulation
        return True

    def get_reminder_message(self, hours_before: int) -> str:
        """
        Génère le message de rappel.
        """
        if hours_before == 24:
            return """⏰ Rappel : Vous avez une réservation demain !

N'oubliez pas votre réservation. Nous vous attendons avec plaisir !

Réf: {reservation_id}
Table: {table_label}
Date: {date}
Heure: {time}"""
        elif hours_before == 2:
            return """⏰ Rappel : Votre réservation est dans 2 heures !

Nous vous attendons avec plaisir !

Réf: {reservation_id}
Table: {table_label}
Date: {date}
Heure: {time}

À tout de suite !"""
        return ""


# Instance globale
_notification_agent: Optional[NotificationAgent] = None


def get_notification_agent() -> NotificationAgent:
    """Retourne l'instance de l'agent notification."""
    global _notification_agent
    if _notification_agent is None:
        _notification_agent = NotificationAgent()
    return _notification_agent


def process_notification(state: ConversationState) -> Dict[str, Any]:
    """Traite une notification."""
    agent = get_notification_agent()
    return agent.process_notification(state)