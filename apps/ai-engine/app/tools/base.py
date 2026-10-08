"""Base pour les outils de l'AI Engine."""

from typing import Any, Dict, Optional, Callable, Awaitable
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger("ai_engine.tools")


class ToolResult(BaseModel):
    """Résultat d'un appel d'outil."""
    success: bool = Field(description="L'opération a-t-elle réussi ?")
    data: Optional[Any] = Field(default=None, description="Données retournées")
    error: Optional[str] = Field(default=None, description="Message d'erreur")
    message: str = Field(description="Message descriptif")


class BaseTool:
    """Classe de base pour tous les outils."""
    
    name: str = Field(description="Nom de l'outil")
    description: str = Field(description="Description de l'outil")
    
    def __init__(self, backend_client: Optional[Any] = None):
        self.backend_client = backend_client
        self.logger = logging.getLogger(f"ai_engine.tools.{self.name}")
    
    def execute(self, **kwargs) -> ToolResult:
        """Exécute l'outil."""
        raise NotImplementedError("Subclasses must implement execute()")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'outil en dictionnaire pour Function Calling."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.get_parameters_schema(),
            }
        }
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Retourne le schéma des paramètres pour Function Calling."""
        raise NotImplementedError("Subclasses must implement get_parameters_schema()")