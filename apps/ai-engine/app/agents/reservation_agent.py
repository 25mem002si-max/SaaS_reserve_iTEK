"""Agent Réservation - Gestion complète des réservations."""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from app.services.llm_service import get_llm_service
from app.prompts.loader import load_prompt
from app.schemas.reservation import ReservationData, ReservationConfirmation, ReservationStatus
from app.schemas.availability import AvailabilityRequest, AvailabilityResult, TableOption
from app.graph.state import ConversationState
from app.config.settings import settings
from app.services.backend_client import BackendClient
from app.services.supervision import get_agent_monitor

logger = logging.getLogger("ai_engine.agents.reservation")


class ReservationAgent:
    """Agent Réservation - Gère le processus complet de réservation."""

    def __init__(self):
        self.llm = get_llm_service()
        self.prompt = load_prompt("reservation")
        self.backend = BackendClient()

    def check_availability(
        self,
        restaurant_id: str,
        date: datetime,
        guests_count: int,
        preferred_zone: Optional[str] = None,
    ) -> Optional[AvailabilityResult]:
        """
        Vérifie les disponibilités pour une date et un nombre de personnes.
        
        NOTE: Cette fonction utilise le service backend (Dev2).
        Pour l'instant, simule des données.
        """
        logger.info(f"🔍 Vérification disponibilité - {restaurant_id}, {date}, {guests_count} personnes")

        if settings.backend_enabled:
            data = self.backend.check_availability({
                "restaurant_id": restaurant_id,
                "date": date.isoformat(),
                "guests_count": guests_count,
                "preferred_zone": preferred_zone,
            })
            return AvailabilityResult.model_validate(data)
        
        # TODO: Appeler le backend Dev2
        # Pour l'instant, simulation
        from app.schemas.availability import TableStatus
        
        # Simuler des tables disponibles
        tables = [
            TableOption(
                table_id="table-001",
                table_label="Table 1",
                capacity=4,
                zone="Intérieur",
                status=TableStatus.AVAILABLE,
            ),
            TableOption(
                table_id="table-002",
                table_label="Table 2",
                capacity=6,
                zone="Terrasse",
                status=TableStatus.AVAILABLE,
            ),
            TableOption(
                table_id="table-003",
                table_label="Table 3",
                capacity=2,
                zone="VIP",
                status=TableStatus.AVAILABLE,
            ),
        ]
        
        # Filtrer par capacité
        available_tables = [t for t in tables if t.capacity >= guests_count]
        
        # Filtrer par zone préférée
        if preferred_zone:
            available_tables = [t for t in available_tables if t.zone == preferred_zone]
        
        return AvailabilityResult(
            restaurant_id=restaurant_id,
            date=date,
            guests_count=guests_count,
            available=len(available_tables) > 0,
            tables=available_tables,
            message=f"{len(available_tables)} table(s) disponible(s)",
        )

    def lock_table(self, table_id: str, restaurant_id: str, duration_seconds: int = 300) -> bool:
        """
        Verrouille une table temporairement.
        
        NOTE: Cette fonction utilise Redis via le backend (Dev2).
        Pour l'instant, simule un verrou.
        """
        logger.info(f"🔒 Verrouillage table {table_id} - {duration_seconds} secondes")
        
        # TODO: Appeler le backend Dev2 pour Redis
        # Pour l'instant, simulation
        if settings.backend_enabled:
            result = self.backend.lock_table(table_id, restaurant_id, duration_seconds)
            return bool(result.get("locked", result.get("success", False)))
        return True

    def unlock_table(self, table_id: str, restaurant_id: str) -> bool:
        """Libère un verrou de table."""
        logger.info(f"🔓 Libération verrou table {table_id}")
        
        if settings.backend_enabled:
            result = self.backend.unlock_table(table_id, restaurant_id)
            return bool(result.get("unlocked", result.get("success", False)))
        return True

    def create_reservation(self, reservation_data: ReservationData, restaurant_id: str) -> Optional[ReservationConfirmation]:
        """
        Crée une réservation définitive.
        
        NOTE: Cette fonction utilise le backend (Dev2).
        """
        logger.info(f"📝 Création réservation - {restaurant_id}")
        
        if settings.backend_enabled:
            data = reservation_data.to_request().model_dump(mode="json")
            data["restaurant_id"] = restaurant_id
            response = self.backend.create_reservation(data)
            return ReservationConfirmation.model_validate(response)

        if reservation_data.is_complete():
            return ReservationConfirmation(
                reservation_id=f"res-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                table_id=reservation_data.table_id or "table-001",
                table_label=reservation_data.table_label or "Table 4",
                customer_name=reservation_data.customer_name or "Client",
                date=reservation_data.date,
                guests_count=reservation_data.guests_count,
                status=ReservationStatus.CONFIRMED if not reservation_data.deposit_required else ReservationStatus.PENDING_PAYMENT,
                deposit_paid=not reservation_data.deposit_required,
                deposit_amount=reservation_data.deposit_amount or 0.0,
                currency=reservation_data.currency or "USD",
                message="✅ Réservation confirmée !",
            )
        return None

    @staticmethod
    def _reservation_datetime(reservation: ReservationData) -> datetime:
        """Combine la date extraite et l'heure choisie par le client."""
        parsed_time = datetime.strptime(reservation.time, "%H:%M").time()
        return reservation.date.replace(
            hour=parsed_time.hour,
            minute=parsed_time.minute,
            second=0,
            microsecond=0,
        )

    def process_reservation(self, state: ConversationState) -> Dict[str, Any]:
        """
        Processus complet de réservation.
        """
        logger.info(f"📅 Processus réservation - {state.get('conversation_id')}")
        monitor = get_agent_monitor()
        monitor.record(
            "reservation_started",
            conversation_id=state.get("conversation_id"),
            restaurant_id=state.get("restaurant_id"),
        )

        intent = state.get("intent")
        if intent and intent.type == "cancel_reservation":
            return {
                "next_action": "end",
                "message": "Je peux annuler votre réservation. Pour éviter toute erreur, pouvez-vous me confirmer la référence de réservation ?",
                "requires_clarification": True,
                "clarification_question": "Quelle est la référence de la réservation à annuler ?",
            }

        if intent and intent.type == "modify_reservation":
            return {
                "next_action": "ask_missing_info",
                "message": "Bien sûr. Quelle information souhaitez-vous modifier : la date, l'heure ou le nombre de personnes ?",
                "requires_clarification": True,
                "clarification_question": "Quelle information souhaitez-vous modifier : la date, l'heure ou le nombre de personnes ?",
            }
        
        # 1. Récupérer les données de réservation
        reservation = state.get("reservation")
        if not reservation:
            return {
                "error": "Aucune donnée de réservation",
                "next_action": "error",
            }

        customer = state.get("customer")
        if customer:
            reservation.customer_name = reservation.customer_name or customer.name
            reservation.customer_phone = reservation.customer_phone or customer.phone
        if not reservation.customer_phone:
            return {
                "next_action": "ask_missing_info",
                "message": "Pour continuer, veuillez me donner votre numéro de téléphone.",
            }
        
        # 2. Vérifier les disponibilités
        reservation.date = self._reservation_datetime(reservation)
        availability = self.check_availability(
            restaurant_id=state.get("restaurant_id", "unknown"),
            date=reservation.date,
            guests_count=reservation.guests_count,
            preferred_zone=reservation.preferred_zone if hasattr(reservation, 'preferred_zone') else None,
        )
        
        if not availability or not availability.available:
            return {
                "availability": availability,
                "next_action": "suggest_alternative",
                "message": "Désolé, aucune table disponible pour ce créneau.",
            }
        
        # 3. Sélectionner la meilleure table
        best_table = availability.get_best_table()
        if not best_table:
            return {
                "availability": availability,
                "next_action": "suggest_alternative",
                "message": "Aucune table ne correspond à vos critères.",
            }
        
        # 4. Verrouiller la table
        locked = self.lock_table(
            table_id=best_table.table_id,
            restaurant_id=state.get("restaurant_id", "unknown"),
        )
        
        if not locked:
            return {
                "availability": availability,
                "next_action": "suggest_alternative",
                "message": "Cette table vient d'être réservée par un autre client.",
            }
        
        # 5. Mettre à jour la réservation avec la table
        reservation.table_id = best_table.table_id
        reservation.table_label = best_table.table_label
        
        # 6. Vérifier si un acompte est requis
        if reservation.guests_count >= 4:
            reservation.deposit_required = True
            reservation.deposit_amount = 10.0  # 10 USD
        else:
            reservation.deposit_required = False
            reservation.deposit_amount = 0.0
        
        # 7. Créer la réservation
        restaurant_id = state.get("restaurant_id", "unknown")
        try:
            confirmation = self.create_reservation(reservation, restaurant_id)
        except Exception as exc:
            logger.error("Création réservation échouée, libération de la table: %s", exc)
            self.unlock_table(best_table.table_id, restaurant_id)
            return {
                "error": "Échec de la création de la réservation",
                "next_action": "retry",
                "message": "La réservation n'a pas pu être créée. Veuillez réessayer.",
            }
        
        if confirmation:
            monitor.record(
                "reservation_created",
                conversation_id=state.get("conversation_id"),
                restaurant_id=restaurant_id,
                reservation_id=confirmation.reservation_id,
            )
            return {
                "reservation_confirmation": confirmation,
                "selected_table": best_table,
                "payment_required": reservation.deposit_required,
                "next_action": "payment" if reservation.deposit_required else "confirmation",
                "message": "Réservation créée avec succès !",
            }
        else:
            self.unlock_table(best_table.table_id, restaurant_id)
            return {
                "error": "Échec de la création de la réservation",
                "next_action": "error",
            }


# Instance globale
_reservation_agent: Optional[ReservationAgent] = None


def get_reservation_agent() -> ReservationAgent:
    """Retourne l'instance de l'agent réservation."""
    global _reservation_agent
    if _reservation_agent is None:
        _reservation_agent = ReservationAgent()
    return _reservation_agent


def process_reservation(state: ConversationState) -> Dict[str, Any]:
    """Traite une réservation."""
    agent = get_reservation_agent()
    return agent.process_reservation(state)