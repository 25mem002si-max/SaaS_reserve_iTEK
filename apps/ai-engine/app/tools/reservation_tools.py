"""Outils de gestion des réservations."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from app.tools.base import BaseTool, ToolResult

# AJout pour l'appel au backend Dev2 par FReddy

from datetime import datetime
from app.config.settings import settings
from app.services.backend_client import BackendClient

class LockTableParams(BaseModel):
    """Paramètres pour lock_table."""
    table_id: str = Field(description="ID de la table à verrouiller")
    restaurant_id: str = Field(description="ID du restaurant")
    duration_seconds: int = Field(default=300, description="Durée du verrouillage en secondes")


class CreateReservationParams(BaseModel):
    """Paramètres pour create_reservation."""
    restaurant_id: str = Field(description="ID du restaurant")
    table_id: str = Field(description="ID de la table")
    customer_name: str = Field(description="Nom du client")
    customer_phone: str = Field(description="Téléphone du client")
    reservation_date: str = Field(description="Date de réservation (YYYY-MM-DD HH:MM)")
    number_of_people: int = Field(description="Nombre de personnes", ge=1, le=50)
    preferences: list = Field(default_factory=list, description="Préférences alimentaires")
    allergies: list = Field(default_factory=list, description="Allergies")
    deposit_amount: float = Field(default=0.0, description="Montant de l'acompte")
    notes: Optional[str] = Field(default=None, description="Notes supplémentaires")


class LockTableTool(BaseTool):
    """Outil pour verrouiller une table temporairement."""
    
    name = "lock_table"
    description = "Verrouille une table temporairement pour éviter les doubles réservations."
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return LockTableParams.model_json_schema()
    
    def execute(self, **kwargs) -> ToolResult:
        try:
            params = LockTableParams(**kwargs)
            
            self.logger.info(f"Verrouillage table {params.table_id}")
            
            # TODO: Appeler le backend Dev2 (Redis)
            # Pour l'instant, simulation
            import random
            locked = random.random() > 0.2
            
            if locked:
                return ToolResult(
                    success=True,
                    data={"lock_token": f"lock-{params.table_id}-{datetime.now().timestamp()}"},
                    message=f"Table {params.table_id} verrouillée pour {params.duration_seconds}s",
                )
            else:
                return ToolResult(
                    success=False,
                    error="TABLE_DEJA_VERROUILLEE",
                    message="La table est déjà verrouillée par un autre client",
                )
                
        except Exception as e:
            self.logger.error(f"Erreur lock_table: {e}")
            return ToolResult(success=False, error=str(e), message="Erreur lors du verrouillage")
    
    def _get_current_time(self):
        from datetime import datetime
        return datetime.now()


class CreateReservationTool(BaseTool):
    """Outil pour créer une réservation définitive."""
    
    name = "create_reservation"
    description = "Crée une réservation définitive dans le système."
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return CreateReservationParams.model_json_schema()
    
    def execute(self, **kwargs) -> ToolResult:
        try:
            params = CreateReservationParams(**kwargs)
            
            self.logger.info(f"Création réservation - {params.customer_name}")
            
            # TODO: Appeler le backend Dev2

            if settings.backend_enabled:
                dt = datetime.fromisoformat(params.reservation_date)  # "YYYY-MM-DD HH:MM"
                data = BackendClient().create_reservation({
                    "restaurant_id": params.restaurant_id,
                    "table_id": params.table_id,
                    "reservation_date": dt.date().isoformat(),
                    "reservation_time": dt.time().isoformat(),
                    "number_of_people": params.number_of_people,
                })
                return ToolResult(
                    success=True,
                    data={
                        "reservation_id": data["id"],
                        "status": data["status"],
                        "table_id": data["table_id"],
                },
                message=f"Réservation {data['id']} créée avec succès",
            )

            # Pour l'instant, simulation
            from datetime import datetime
            reservation_id = f"res-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            return ToolResult(
                success=True,
                data={
                    "reservation_id": reservation_id,
                    "status": "CONFIRMED",
                    "table_id": params.table_id,
                    "qr_code_token": f"qr-{reservation_id}",
                },
                message=f"Réservation {reservation_id} créée avec succès",
            )
                
        except Exception as e:
            self.logger.error(f"Erreur create_reservation: {e}")
            return ToolResult(success=False, error=str(e), message="Erreur lors de la création")