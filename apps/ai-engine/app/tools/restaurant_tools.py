"""Outils pour les informations du restaurant."""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from app.tools.base import BaseTool, ToolResult


class GetRestaurantMenuParams(BaseModel):
    """Paramètres pour get_restaurant_menu."""
    restaurant_id: str = Field(description="ID du restaurant")


class GetRestaurantMenuTool(BaseTool):
    """Outil pour récupérer le menu du restaurant."""
    
    name = "get_restaurant_menu"
    description = "Récupère le menu complet du restaurant."
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        return GetRestaurantMenuParams.model_json_schema()
    
    def execute(self, **kwargs) -> ToolResult:
        try:
            params = GetRestaurantMenuParams(**kwargs)
            
            self.logger.info(f"Récupération menu - {params.restaurant_id}")
            
            # TODO: Appeler le backend Dev2
            # Pour l'instant, simulation
            menu = {
                "categories": [
                    {
                        "name": "Entrées",
                        "items": [
                            {"id": "e1", "name": "Salade Congolaise", "price": 8.0},
                            {"id": "e2", "name": "Beignets de Banane", "price": 6.0},
                        ]
                    },
                    {
                        "name": "Plats",
                        "items": [
                            {"id": "p1", "name": "Poulet Yassa", "price": 12.0},
                            {"id": "p2", "name": "Poisson Braisé", "price": 15.0},
                            {"id": "p3", "name": "Riz à la Viande", "price": 10.0},
                        ]
                    },
                    {
                        "name": "Desserts",
                        "items": [
                            {"id": "d1", "name": "Fruit de Saison", "price": 4.0},
                            {"id": "d2", "name": "Gâteau au Chocolat", "price": 5.0},
                        ]
                    },
                    {
                        "name": "Boissons",
                        "items": [
                            {"id": "b1", "name": "Jus de Fruit", "price": 3.0},
                            {"id": "b2", "name": "Soda", "price": 2.0},
                            {"id": "b3", "name": "Bière", "price": 4.0},
                        ]
                    }
                ]
            }
            
            return ToolResult(
                success=True,
                data=menu,
                message="Menu récupéré avec succès",
            )
                
        except Exception as e:
            self.logger.error(f"Erreur get_restaurant_menu: {e}")
            return ToolResult(success=False, error=str(e), message="Erreur lors de la récupération du menu")