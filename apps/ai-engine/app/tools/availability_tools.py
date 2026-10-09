"""Outils de vérification de disponibilité."""

from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from app.tools.base import BaseTool, ToolResult
from app.schemas.availability import AvailabilityRequest, AvailabilityResult
# AJout pour l'appel au backend Dev2

from app.config.settings import settings
from app.services.backend_client import BackendClient

class CheckAvailabilityParams(BaseModel):
    """Paramètres pour check_availability."""
    restaurant_id: str = Field(description="ID du restaurant")
    reservation_date: str = Field(description="Date au format YYYY-MM-DD")
    reservation_time: str = Field(description="Heure au format HH:MM")
    number_of_people: int = Field(description="Nombre de personnes", ge=1, le=50)
    preferred_zone: Optional[str] = Field(default=None, description="Zone préférée (VIP, Terrasse, Intérieur)")


class CheckAvailabilityTool(BaseTool):
    """Outil pour vérifier la disponibilité des tables."""
    
    name = "check_availability"
    description = "Vérifie les tables disponibles pour une date, une heure et un nombre de personnes."
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return CheckAvailabilityParams.model_json_schema()
    
    def execute(self, **kwargs) -> ToolResult:
        """Exécute la vérification de disponibilité."""
        try:
            # Valider les paramètres
            params = CheckAvailabilityParams(**kwargs)
            
            self.logger.info(f"Vérification disponibilité - {params.restaurant_id}, {params.reservation_date} {params.reservation_time}")
            # TODO: Appeler le backend Dev2
            # Ajout pour verification de la disponibilite de la table

            if settings.backend_enabled:
                data = BackendClient().check_availability(
                    params.restaurant_id,
                    {
                        "reservation_date": params.reservation_date,
                        "reservation_time": params.reservation_time,
                        "number_of_people": params.number_of_people,
                    },
                )
                tables = [
                    {"id": t["id"], "label": f"Table {t['table_number']}", "capacity": t["capacity"]}
                    for t in data["available_tables"]
                ]
                if not tables:
                    return ToolResult(
                        success=False,
                        error="AUCUNE_TABLE_DISPONIBLE",
                        message="Aucune table disponible pour ce créneau",
                )
                return ToolResult(
                    success=True,
                    data={"tables": tables, "available": True},
                    message="Tables disponibles trouvées",
                )


            
            # Pour l'instant, simulation
            import random
            
            # Simuler des tables disponibles
            available = random.random() > 0.3
            
            if available:
                return ToolResult(
                    success=True,
                    data={
                        "tables": [
                            {"id": "t1", "label": "Table 1", "capacity": 4, "zone": "Intérieur"},
                            {"id": "t2", "label": "Table 2", "capacity": 6, "zone": "Terrasse"},
                        ],
                        "available": True,
                    },
                    message="Tables disponibles trouvées",
                )
            else:
                return ToolResult(
                    success=False,
                    error="AUCUNE_TABLE_DISPONIBLE",
                    message="Aucune table disponible pour ce créneau",
                )
                
        except Exception as e:
            self.logger.error(f"Erreur check_availability: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                message="Erreur lors de la vérification des disponibilités",
            )